from mycroft.skills.core import MycroftSkill, intent_file_handler
from adventure import load_advent_dat
from adventure.game import Game
from os.path import exists, expanduser
from padatious import IntentContainer
import time


class ColossalCaveAdventureSkill(MycroftSkill):
    save_file = "/cave_adventure.save"
    playing = False
    container = None
    game = Game()

    def initialize(self):
        load_advent_dat(self.game)
        self.last_interaction = time.time()
        self._init_padatious()
        self.disable_intent("save.intent")

    def _init_padatious(self):
        # i want to check in converse method if some intent by this skill will trigger
        # however there is no mechanism to query the intent parser
        # PR incoming
        intent_cache = expanduser(self.config_core['padatious']['intent_cache'])
        self.container = IntentContainer(intent_cache)
        # ignoring credits intent on purpose
        for intent in ["save.intent", "restore.intent"]:
            name = str(self.skill_id) + ':' + intent
            filename = self.find_resource(intent, 'vocab')
            if exists(filename):
                with open(filename, "r") as f:
                    self.container.add_intent(name, f.readlines())
        self.container.train()

    def will_trigger(self, utterance):
        # check if self will trigger for given utterance
        intent = self.container.calc_intent(utterance)
        if intent.conf < 0.5:
            return False
        return True

    def get_intro_message(self):
        """ Get a message to speak on first load of the skill.

        Useful for post-install setup instructions.

        Returns:
            str: message that will be spoken to the user
        """
        self.speak_dialog("thank.you")
        return None

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
        line = line.replace("\n", " ").replace("(", "").replace(")", "").replace("etc.", "etc")
        lines = line.split(".")
        for line in lines:
            self.speak(line.strip(), expect_response=True, wait=True)
        self.last_interaction = time.time()
        self.maybe_end_game()

    def handle_credits(self, message=None):
        self.speak_dialog("credits")

    @intent_file_handler("play.intent")
    def handle_play(self, message=None):
        self.playing = True
        self.enable_intent("save.intent")
        self.game.start()
        self.speak_output(self.game.output)

    @intent_file_handler("save.intent")
    def handle_save(self, message=None):
        if not self.playing:
            self.speak_dialog("save.not.found")
        else:
            self.game.save(self.save_file)
            self.speak_dialog("game.saved")

    @intent_file_handler("restore.intent")
    def handle_restore(self, message):
        if exists(self.save_file):
            self.playing = True
            self.game.resume(self.save_file)
            self.speak_dialog("restore.game")
        else:
            self.speak_dialog("save.not.found")
            new_game = self.ask_yesno("new.game")
            if new_game:
                self.handle_play()

    def maybe_end_game(self):
        # end game if no interaction for 10 mins
        if self.playing:
            timed_out = time.time() - self.last_interaction > 10*3600
            # disable save and gameplay
            if self.game.is_finished or timed_out:
                self.disable_intent("save.intent")
                self.playing = False
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
            if self.will_trigger(ut):
                # save / restore will trigger
                return False
            # capture speech and pipe to the game
            words = ut.split(" ")
            if words:
                self.speak_output(self.game.do_command(words))
                return True
        return False


def create_skill():
    return ColossalCaveAdventureSkill()
