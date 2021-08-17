import sys


def _wrap_with(code):

    def inner(text, bold=False):
        c = code
        if bold:
            c = "1;%s" % c
        return "\033[%sm%s\033[0m" % (c, text)
    return inner


red_text = _wrap_with('31')
green_text = _wrap_with('32')
yellow_text = _wrap_with('33')
blue_text = _wrap_with('34')
magenta_text = _wrap_with('35')
cyan_text = _wrap_with('36')
white_text = _wrap_with('37')


def eprint(o, bold=True, separator=' ', end='\n', flush=False):
    print("[!] " + red_text(o, bold=bold), sep=separator,
          end=end, flush=flush, file=sys.stderr)


def warning_print(o, bold=True, separator=' ', end='\n', flush=False):
    print(yellow_text(o, bold=bold), sep=separator,
          end=end, flush=flush, file=sys.stderr)


def success_print(o, bold=True, separator=' ', end='\n', flush=False):
    print(green_text(o, bold=bold), sep=separator,
          end=end, flush=flush, file=sys.stderr)


def status_print(o, bold=True, separator=' ', end='\n', flush=False):
    print(cyan_text(o, bold=bold), sep=separator,
          end=end, flush=flush, file=sys.stderr)


def default_print(o, bold=True, separator=' ', end='\n', flush=False):
    print("-- " + white_text(o, bold=bold), sep=separator,
          end=end, flush=flush, file=sys.stderr)


def print_color(o, color_fn, bold=False):
    print(color_fn(o, bold=bold))


def confirm_prompt(prompt_fn, yes='y', no='n'):
    prompt_fn()
    opt = input()

    while opt != yes and opt != no:
        prompt_fn()
        opt = input()

    return opt == yes
