#!/usr/bin/env python3

import argparse

from runes_client import ui_param

parser = argparse.ArgumentParser(description="Connect to DAWNet server.")
parser.add_argument("token", help="Token for DAWNet server connection")
args = parser.parse_args()

import runes_client as rune
from runes_client.core import RunesFilePath


@ui_param("a", "RunesNumberSlider", min=0, max=10, step=1, default=5)
# @ui_param('c', 'RunesMultiChoice', options=['cherries', 'oranges', 'grapes'], default='grapes')
async def method_to_register(a: int, b: RunesFilePath, c: bool = False):
    try:
        print(f"Input A: {a}")
        print(f"Input B: {b}")

        # DO INFERENCE SHIT HERE

        await rune.output().add_file(b)
        await rune.output().add_message("This is a message send to the plugin")

        return True
    except Exception as e:
        await rune.output().add_error(f"This is an error sent to the plugin: {e}")

        return False


rune.set_input_target_format("wav")
rune.set_input_target_channels(2)
rune.set_input_target_sample_rate(44100)
rune.set_input_target_bit_depth(16)

rune.set_output_target_format("wav")
rune.set_output_target_channels(2)
rune.set_output_target_sample_rate(44100)
rune.set_output_target_bit_depth(16)

rune.set_token(token=args.token)
rune.set_name("Rune AI Template")
rune.set_description(
    "This is a template intended as a starting place to create custom Rune AI functions."
)
rune.register_method(method_to_register)


print("REGISTERED TOKEN & " + str(method_to_register))
rune.connect_to_server()
