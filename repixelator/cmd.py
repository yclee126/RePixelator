import sys

def cmd():
    args = sys.argv[1:]
    from .repixelator import main
    main(args)

def gui():
    from .repixelator_gui import main
    main()