#!/usr/bin/env python3
"""Make route-page meta descriptions and FAQ counts natural (one-time patch).

Replaces the mechanical "{origin} to {destination} bus timings, operators,
stoppages. 1 buses listed..." description in scripts/gen_seo_pages.py with a
natural sentence, and fixes the "1 bus services are listed" grammar bug in
the FAQ answer. Idempotent: safe to run again.
"""
import py_compile

P = "scripts/gen_seo_pages.py"

OLD_DESC = '''    description = f"{origin} to {destination} bus timings, operators, stoppages. {count} buses listed. First {first}, last {last}."[:300]'''

NEW_DESC = '''    bus_word = "bus" if count == 1 else "buses"
    ops = [o for o in operators if o and o.strip() and o.strip() not in ("\u2014", "-")][:3]
    run_by = (" Run by " + ", ".join(ops) + ".") if ops else ""
    if stats["first"] is None:
        description = f"{origin} to {destination} bus time table with routes, stoppages and operators on {SITE_NAME}."[:300]
    elif count == 1:
        description = f"{origin} to {destination} bus time table \u2014 1 bus daily at {first}.{run_by} Timings and stoppages on {SITE_NAME}."[:300]
    else:
        description = f"{origin} to {destination} bus time table \u2014 {count} {bus_word} daily, first {first}, last {last}.{run_by} Timings and stoppages on {SITE_NAME}."[:300]'''

OLD_FAQ = '''{count} bus services are listed on this route.'''
NEW_FAQ = '''{count} bus " + ('service is' if count == 1 else 'services are') + " listed on this route.'''


def main():
    src = open(P, encoding="utf-8").read()
    changed = False
    if OLD_DESC in src:
        src = src.replace(OLD_DESC, NEW_DESC, 1)
        changed = True
        print("meta description: patched")
    elif "bus time table \u2014" in src and "run_by" in src:
        print("meta description: already patched")
    else:
        raise SystemExit("ANCHOR MISSING for description - aborting")

    if OLD_FAQ in src:
        src = src.replace(OLD_FAQ, NEW_FAQ, 1)
        changed = True
        print("FAQ count grammar: patched")
    elif "service is' if count == 1" in src:
        print("FAQ count grammar: already patched")
    else:
        raise SystemExit("ANCHOR MISSING for FAQ count - aborting")

    if changed:
        with open(P, "w", encoding="utf-8") as f:
            f.write(src)
    py_compile.compile(P, doraise=True)
    print("compile OK, changed:", changed)


if __name__ == "__main__":
    main()
