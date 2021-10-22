import time
from os.path import exists, expanduser

from adapt.intent import IntentBuilder
from mycroft.skills.core import MycroftSkill, intent_file_handler
from mycroft.skills.core import intent_handler
from mycroft.skills.intent_service_interface import IntentQueryApi
from ovos_workshop.skills import OVOSSkill
from ovos_workshop.skills.decorators import layer_intent, enables_layer, \
    disables_layer, resets_layers
from .adventure import load_advent_dat
from .adventure.game import Game


class ColossalCaveAdventureSkill(OVOSSkill):

    def __init__(self):
        super().__init__()
        self.playing = False
        self.game = None
        self.last_interaction = time.time()
        # TODO xdg path
        self.save_file = expanduser("~/cave_adventure.save")

    def initialize(self):
        # start skill in "not_playing" layer
        self.intent_layers.disable()
        self.intent_layers.activate_layer("not_playing")

    def will_trigger(self, utterance, lang):
        # will an intent from this skill trigger ?
        skill_id = IntentQueryApi(self.bus).get_skill(utterance, lang)
        if skill_id and skill_id == self.skill_id:
            return True
        return False

    @enables_layer("playing")
    def start_game(self):
        self.playing = True
        self.game = Game()
        load_advent_dat(self.game)
        self.last_interaction = time.time()
        self.game.start()
        self.speak_output(self.game.output)

    def speak_output(self, line):
        # dont speak parts of the intro
        # replace type with say because its voice game
        # re join words split across lines
        # reformat \n and separate by sentence
        line = line.lower().replace("type", "say").replace("-\n", "")
        line = line.replace(
            '  i should warn\nyou that i look at only the first five letters of each word, so you\'ll\nhave to enter "northeast" as "ne" to distinguish it from "north".',
            "")
        line = line.replace(
            "- - this program was originally developed by willie crowther.  most of the\nfeatures of the current program were added by don woods (don @ su-ai).\ncontact don if you have any questions, comments, etc.",
            "")
        line = line.replace("\n", " ").replace("(", "").replace(")",
                                                                "").replace(
            "etc.", "etc")
        lines = line.split(".")
        for line in lines:
            if line.strip():
                self.speak(line.strip())
        self.last_interaction = time.time()
        self.maybe_end_game()
        # HACK this is a workaround for a core bug, skill is only booted
        # to top of converse list after next intent interaction
        self.make_active()

    @layer_intent("play.intent", layer_name="not_playing")
    def handle_play(self, message=None):
        self.start_game()

    @layer_intent("restart_game.intent", layer_name="playing")
    def handle_restart(self, message=None):
        # shorter intent that doesnt require game name in utt
        self.start_game()

    @layer_intent("save.intent", layer_name="playing")
    def handle_save(self, message=None):
        if not self.playing:
            self.speak_dialog("save.not.found")
        else:
            with open(self.save_file, "wb") as f:
                self.game.t_suspend("save", f)
                self.speak_dialog("game.saved")

    @layer_intent("resume_game_short.intent", layer_name="playing")
    def handle_resume(self, message=None):
        # shorter intent that doesnt require game name in utt
        self.handle_restore(message)

    @intent_file_handler("restore.intent")
    def handle_restore(self, message):
        if exists(self.save_file):
            self.playing = True
            self.game = Game.resume(self.save_file)
            self.speak_dialog("restore.game")
        else:
            self.speak_dialog("save.not.found")
            new_game = self.ask_yesno("new.game")
            if new_game:
                self.start_game()

    @resets_layers()
    def game_over(self):
        self.disable_intent("Save")
        self.playing = False
        self.game = Game()
        load_advent_dat(self.game)

    def maybe_end_game(self):
        # end game if no interaction for 10 mins
        if self.playing:
            timed_out = time.time() - self.last_interaction > 10 * 3600
            # disable save and gameplay
            if self.game.is_finished or timed_out:
                self.game_over()
            # save game to allow restoring if timedout
            if timed_out:
                self.handle_save()

    def converse(self, utterances, lang="en-us"):
        """ Handle conversation.

        This method gets a peek at utterances before the normal intent
        handling process after a skill has been invoked once.

        To use, override the converse() method and return True to
        indicate that the utterance has been handled.

        Args:
            utterances (list): The utterances from the user
            lang:       language the utterance is in

        Returns:
            bool: True if an utterance was handled, otherwise False
        """
        # check if game was abandoned midconversation and we should clean it up
        self.maybe_end_game()
        if self.playing:
            ut = utterances[0]
            # if self will trigger do nothing and let intents handle it
            if self.will_trigger(ut, lang):
                # save / restore will trigger
                return False
            # capture speech and pipe to the game
            words = ut.split(" ")
            self.speak_output(self.game.do_command(words))
            self.make_active()
            return True
        return False


def create_skill():
    return ColossalCaveAdventureSkill()
