# Times I forgot to add something important: v4
#
# Copyright (c) 2024 Chris Mackey
# There is no warranty.
# I'm not liable for anything related to the use of this software.
# You can use, copy and modify this software for personal use.
# You may redistribute this software as long as:
#  - it is unmodified.
#  - it is provided for free.
# All other rights reserved.

# version 4: don't backup if the orders have changed, only backup if turn file changed
# version 3: move static map files to the maps directory, only copy turn/order/other files that change
# version 2: added loop to continually check saves while the script is running

# user configurable values
autosave_min = 1 						# minutes between save checks. 0 will disable continuous checks
autosave_prefix = "_autosave_"			# filename prefix for the latest automatically saved file
archive_prefix = "__archive_"			# filename prefix for archived save files
datetime_postfix = "_%Y-%m-%d_%H-%M-%S" # datetime format for archived save files

# The further down you go, the further your chances are for breaking something. Here be dragons. (have fun)

import os
import sys
import time
import shutil
import filecmp
from datetime import datetime


# by default this will check for saved games in the location where it's placed 
# windows default savegame location: %appdata%/Dominions6/savedgames
# if a path is provided through the first command line argument, use that instead
if len(sys.argv) > 1: savedgames_dir = sys.argv[1]
else: savedgames_dir = os.path.dirname(sys.argv[0])

# gets the list of currently available games
def save_updated_games():
	print("==============================================================")
	print("Checking games for updates")
	for savedgame in os.scandir(savedgames_dir):
		if (os.path.isdir(savedgame) 
			and not savedgame.name.startswith(autosave_prefix) 
			and not savedgame.name.startswith(archive_prefix)):
			compare_saves(savedgame.name)

# checks to see if the game state has changed since the last save
# save only if the current saved game is different from the latest autosave
def compare_saves(savedgame):
	current_path = os.path.join(savedgames_dir, savedgame)
	save_path = os.path.join(savedgames_dir, autosave_prefix + savedgame)
	map_path = os.path.join(savedgames_dir, "../maps", savedgame)

	if not os.path.exists(map_path):
		migrate_maps(savedgame)

	if not os.path.exists(save_path):
		print("Setting up autosaves for " + savedgame)
		save_game(savedgame)
		return
	
	comparison = filecmp.dircmp(current_path, save_path)

	if comparison.diff_files:
		print(savedgame + " has pending changes: " + ", ".join(comparison.diff_files))
		newturn = False
		for f in comparison.diff_files:
			if f.endswith(".trn"): newturn = True
		if newturn:
			save_game(savedgame)
	else:
		print(savedgame + " has no pending changes.")

# moves the map files from the saved games folder to the maps folder to prevent redundant copying
# WARNING: I'm just assuming anything not explicitly excluded is part of the map
def migrate_maps(savedgame):
	current_path = os.path.join(savedgames_dir, savedgame)
	map_path = os.path.join(savedgames_dir, "../maps", savedgame)

	print("Migrating " + savedgame + " map files from savedgames to maps")
	os.mkdir(map_path)
	for gamefile in os.scandir(current_path):
		# pretender file? only exists on the host machine
		if gamefile.name == "ftherlnd": continue

		# orders file. records all user planned actions for current turn
		if gamefile.name.endswith(".2h"): continue

		# turn file. contains the game state information for the current turn
		if gamefile.name.endswith(".trn"): continue

		# everything else prolly is part of the map, so move it
		shutil.move(os.path.join(savedgames_dir, savedgame, gamefile.name), map_path)

# copies the current turn into an autosave, archiving the latest autosave if necessary
def save_game(savedgame):
	current_path = os.path.join(savedgames_dir, savedgame)
	save_path = os.path.join(savedgames_dir, autosave_prefix + savedgame)

	if os.path.exists(save_path):
		archive_save(savedgame)
		shutil.rmtree(save_path) # remove current save folder just to be sure everything is clean

	print("Saving " + savedgame)
	shutil.copytree(current_path, save_path)

# copies the latest autosave to an archived one bearing a timestamp
def archive_save(savedgame):
	save_path = os.path.join(savedgames_dir, autosave_prefix + savedgame)
	archive_path = os.path.join(savedgames_dir, archive_prefix + savedgame + datetime.today().strftime(datetime_postfix))
	
	print("Archiving previous " + savedgame + " save")
	shutil.copytree(save_path, archive_path)

# start of actual execution
print("Using savedgames path: " + savedgames_dir)

if autosave_min == 0: save_updated_games()
while(autosave_min > 0):
	save_updated_games()
	time.sleep(autosave_min * 60)
