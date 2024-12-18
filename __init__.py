from pyfrotz.ovos import FrotzSkill
from pyfrotz.parsers import advent_intro_parser


class ColossalCaveAdventureSkill(FrotzSkill):
    def __init__(self, *args, **kwargs):
        # game is english only, apply bidirectional translation
        # TODO - dedicated icon, use pyfrotz icon for now
        skill_icon = "https://raw.githubusercontent.com/TigreGotico/pyFrotz/refs/heads/dev/pyfrotz/gui/all/pyfrotz.png"
        bg = "https://raw.githubusercontent.com/TigreGotico/pyFrotz/refs/heads/dev/pyfrotz/gui/all/bg.png"
        super().__init__(*args,
                         game_id="Advent",
                         game_lang="en-us",
                         game_data=f'{self.root_dir}/res/{self.game_id}.z5',
                         intro_parser=advent_intro_parser,
                         skill_icon=skill_icon,
                         game_image=bg,
                         **kwargs)
