# Windows System Diagnostics

A utility script to automate diagnostics and UI interactions. 

## Commands

Here are all the available commands and arguments you can use when running `main.py`:

### Standard Bot Mode
Runs the main automation loop. It monitors and acts on UI elements like 'Events', 'Search', 'Attack', and 'March'.
* `python main.py`
  Runs the standard bot mode with the default squad limit (4 squads).
* `python main.py <N>`
  Runs the standard bot mode but limits the number of active squads to `N` (e.g., `python main.py 2`).

### Configuration Mode
Use this to calibrate the bot or set up screen templates for the first time.
* `python main.py --config-run`
  Starts the full configuration flow to set up custom templates.
* `python main.py --config-run=<target>`
  Starts calibration for a specific target element only. Available targets are:
  * `events_button` - Events Button (usually top right menu)
  * `search` - Search Button (rectangular button)
  * `attack_button` - Attack Button (after clicking a zombie)
  * `march_button` - March/Send Squad Button
  * `quit_game_menu` - Quit Game Menu (press ESC in game first to show it)
  * `go_status` - The small "Go" or "Marching" button indicator
  * `stamina_empty` - Stamina Empty / Use Stamina Item popup button

### Clicker Mode
A rapid auto-clicking utility mode. You move the mouse manually, and the script handles the clicking.
* `python main.py --clicker`
  Runs the button clicker at a default speed of 50 clicks per second.
* `python main.py --clicker=<N>`
  Runs the button clicker at `N` clicks per second (e.g., `python main.py --clicker=2` for 2 clicks a second).

> **Note:** To stop the script in any mode, you can hold the **`q`** key, or quickly press **Alt+Tab** and **Ctrl+C** in the terminal window.
