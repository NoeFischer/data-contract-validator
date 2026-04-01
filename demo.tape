Output demo.gif

Set Shell "zsh"
Set FontSize 14
Set Width 900
Set Height 580
Set Padding 16
Set BorderRadius 8
Set WindowBar Rings
Set WindowBarSize 36
Set Theme "Dracula"
Set TypingSpeed 40ms
Set Framerate 24

Hide
Type "cd $(git rev-parse --show-toplevel) && source .venv/bin/activate"
Enter
Sleep 800ms
Show

Type "validate-contract -c contracts/customers_v1.yaml -d data/customers_sample.csv"
Sleep 600ms
Enter
Sleep 4s
