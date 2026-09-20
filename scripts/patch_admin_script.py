#!/usr/bin/env python3
"""Fix admin.html: the BLOG_TMPL template literal contains literal </script>
tags (GA gtag block) which terminate the browser's outer <script> element,
killing all admin JS (login button does nothing). Escape them as <\\/script>
so the template still emits valid </script> in generated blog pages."""

def main():
    h = open('admin.html', encoding='utf-8').read()
    if '<\\/script>' in h:
        print('admin.html: already fixed')
        return
    old1 = '<script async src="https://www.googletagmanager.com/gtag/js?id=G-L4E3D1YX9X"></script>'
    new1 = '<script async src="https://www.googletagmanager.com/gtag/js?id=G-L4E3D1YX9X"><\\/script>'
    assert h.count(old1) == 1, 'ga async tag anchor not found: %d' % h.count(old1)
    h = h.replace(old1, new1)
    old2 = "  gtag('config', 'G-L4E3D1YX9X');\n</script>"
    new2 = "  gtag('config', 'G-L4E3D1YX9X');\n<\\/script>"
    assert h.count(old2) == 1, 'ga config close anchor not found: %d' % h.count(old2)
    h = h.replace(old2, new2)
    open('admin.html', 'w', encoding='utf-8').write(h)
    print('admin.html: blog template </script> tags escaped')

if __name__ == '__main__':
    main()
