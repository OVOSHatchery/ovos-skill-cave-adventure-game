from pyfrotz.ovos import FrotzSkill
from pyfrotz.parsers import advent_intro_parser


class ColossalCaveAdventureSkill(FrotzSkill):
    def __init__(self, *args, **kwargs):
        # game is english only, apply bidirectional translation
        super().__init__(*args,
                         game_id="Advent",
                         game_lang="en-us",
                         game_data=f'{self.root_dir}/res/{self.game_id}.z5',
                         intro_parser=advent_intro_parser,
                         **kwargs)
