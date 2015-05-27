import os
import fnmatch

def Walk(root='.', recurse=True, pattern='*'):
    for path, subdirs, files in os.walk(root):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                yield os.path.join(path, name)
        if not recurse:
            break

def LOC_py(root=''):
    """
        Counts lines of code in two ways:
            maximal size (source LOC) with blank lines and comments
            minimal size (logical LOC) stripping same

        Sums all Python files in the specified folder.
        By default recurses through subfolders.
    """
    count_mini, count_maxi = 0, 0
    for fspec in Walk(root, True, '*.py'):
        print "#", fspec,
        skip = False
        current_mini = 0
        current_maxi = 0
        for line in open(fspec).readlines():
            count_maxi += 1
            current_maxi += 1
            
            line = line.strip()
            if line:
                if line.startswith('#'):
                    continue
                if line.startswith('"""'):
                    skip = not skip
                    continue
                if not skip:
                    count_mini += 1
                    current_mini += 1
        print "MIN: ", current_mini, " MAX: ", current_maxi

    return count_mini, count_maxi

def LOC_html(root=''):
    """
        Counts lines of code in two ways:
            maximal size (source LOC) with blank lines and comments
            minimal size (logical LOC) stripping same

        Sums all Python files in the specified folder.
        By default recurses through subfolders.
    """
    count_mini, count_maxi = 0, 0
    for fspec in Walk(root, True, '*.html'):
        print "#", fspec, 
        current_mini = 0
        current_maxi = 0
        for line in open(fspec).readlines():
            count_maxi += 1
            current_maxi += 1
            
            line = line.strip()
            if line:
                count_mini += 1
                current_mini += 1
        print "MIN: ", current_mini, " MAX: ", current_maxi

    return count_mini, count_maxi

print LOC_py(root='.'), " python lines ===="
print LOC_html(root='./static/'), " html lines ===="