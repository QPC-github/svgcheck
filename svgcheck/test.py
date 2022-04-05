import pycodestyle
import unittest
import os
import shutil
import lxml.etree
import subprocess
import six
import sys
from rfctools_common.parser import XmlRfcParser
from rfctools_common import log
import difflib
from svgcheck.checksvg import checkTree
import io

test_program = "svgcheck"


def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None


class Test_Coding(unittest.TestCase):
    def test_pycodestyle_conformance(self):
        """Test that we conform to PEP8."""
        pep8style = pycodestyle.StyleGuide(quiet=False, config_file="pycode.cfg")
        result = pep8style.check_files(['run.py', 'checksvg.py', 'test.py', 'word_properties.py'])
        self.assertEqual(result.total_errors, 0,
                         "Found code style errors (and warnings).")

    def test_pyflakes_confrmance(self):
        p = subprocess.Popen(['pyflakes', 'run.py', 'checksvg.py', 'test.py',
                              'word_properties.py'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (stdoutX, stderrX) = p.communicate()
        ret = p.wait()
        if ret > 0:
            if six.PY3:
                stdoutX = stdoutX.decode('utf-8')
                stderrX = stderrX.decode('utf-8')
            print(stdoutX)
            print(stderrX)
            self.assertEqual(ret, 0)


class TestCommandLineOptions(unittest.TestCase):
    """ Run a set of command line checks to make sure they work """
    def test_get_version(self):
        check_process(self, [sys.executable, test_program, "--version"],
                      "Results/version.out", "Results/version.err",
                      None, None)

    def test_clear_cache(self):
        if not os.path.exists('Temp'):
            os.mkdir('Temp')
        if not os.path.exists('Temp/cache'):
            os.mkdir('Temp/cache')
        shutil.copy('Tests/cache_saved/reference.RFC.1847.xml',
                    'Temp/cache/reference.RFC.1847.xml')
        check_process(self, [sys.executable, test_program, "--clear-cache",
                             "--cache=Temp/cache"],
                      None, None,
                      None, None)
        self.assertFalse(os.path.exists('Temp/cache/reference.RFC.1847.xml'))


class TestParserMethods(unittest.TestCase):

    def test_circle(self):
        """ Tests/circle.svg: Test a simple example with a small number of required edits """
        test_svg_file(self, "circle.svg")

    def test_rbg(self):
        """ Tests/rgb.svg: Test a simple example with a small number of required edits """
        test_svg_file(self, "rgb.svg")

    def test_dia_sample(self):
        """ Tests/dia-sample-svg.svg: Generated by some unknown program """
        test_svg_file(self, "dia-sample-svg.svg")

    def test_drawberry_sample(self):
        """ Tests/drawberry-sample-2.svg: Generated by DrawBerry """
        test_svg_file(self, "DrawBerry-sample-2.svg")

    def test_example_dot(self):
        """ Tests/example-dot.svg """
        test_svg_file(self, "example-dot.svg")

    def test_httpbis_proxy(self):
        """ Tests/httpbis-proxy20-fig6.svg """
        test_svg_file(self, "httpbis-proxy20-fig6.svg")

    def test_ietf_test(self):
        """ Tests/IETF-test.svg """
        test_svg_file(self, "IETF-test.svg")

    def test_svg_wordle(self):
        """ Tests/svg-wordle.svg """
        test_svg_file(self, "svg-wordle.svg")

    def test_svg_malformed(self):
        """ Tests/malformed.svg """
        test_svg_file(self, "malformed.svg")

    @unittest.skipIf(os.name != 'nt', "xi:include does not work correctly on Linux")
    def test_rfc(self):
        """ Tests/rfc.xml: Test an XML file w/ two pictures """
        test_rfc_file(self, "rfc.xml")

    def test_simple_sub(self):
        if not os.path.exists('Temp'):
            os.mkdir('Temp')
        check_process(self, [sys.executable, test_program, "--out=Temp/rfc.xml",
                             "--repair", "--no-xinclude", "Tests/rfc.xml"],
                      "Results/rfc-01.out", "Results/rfc-01.err",
                      "Results/rfc-01.xml", "Temp/rfc.xml")

    def test_to_stdout(self):
        check_process(self, [sys.executable, test_program, "--repair", "--no-xinclude",
                             "Tests/rfc.xml"], "Results/rfc-02.out", "Results/rfc-02.err",
                      None, None)

    def test_always_to_stdout(self):
        check_process(self, [sys.executable, test_program, "--always-emit", "--no-xinclude",
                             "Tests/good.svg"], "Results/colors.out", "Results/good.err",
                      None, None)

    def test_always2_to_stdout(self):
        check_process(self, [sys.executable, test_program, "--always-emit", "--no-xinclude",
                             "Tests/colors.svg"], "Results/colors.out", "Results/colors.err",
                      None, None)

    def test_to_quiet(self):
        check_process(self, [sys.executable, test_program, "--no-xinclude", "--quiet",
                             "Tests/rfc.xml"], "Results/rfc-03.out",
                      "Results/rfc-03.err", None, None)

    def test_rfc_complete(self):
        check_process(self, [sys.executable, test_program, "--repair", "Tests/rfc-svg.xml"],
                      "Results/rfc-svg.out", "Results/rfc-svg.err", None, None)

    def test_colors(self):
        check_process(self, [sys.executable, test_program, "-r", "Tests/colors.svg"],
                      "Results/colors.out", "Results/colors.err", None, None)

    def test_full_tiny(self):
        if not os.path.exists('Temp'):
            os.mkdir('Temp')
        check_process(self, [sys.executable, test_program, "--out=Temp/full-tiny.xml",
                             "--repair", "Tests/full-tiny.xml"],
                      "Results/full-tiny.out", "Results/full-tiny.err",
                      "Results/full-tiny.xml", "Temp/full-tiny.xml")
        print("pass 2")
        check_process(self, [sys.executable, test_program, "--out=Temp/full-tiny-02.xml",
                             "Temp/full-tiny.xml"],
                      "Results/full-tiny-02.out", "Results/full-tiny-02.err",
                      None, None)

    def test_utf8(self):
        check_process(self, [sys.executable, test_program, "-r", "Tests/utf8.svg"],
                      "Results/utf8.out", "Results/utf8.err", None, None)

    def test_twice(self):
        if not os.path.exists('Temp'):
            os.mkdir('Temp')
        check_process(self, [sys.executable, test_program, "-r", "--out=Temp/utf8-1.svg",
                             "Tests/utf8.svg"],
                      "Results/empty", "Results/utf8.err", None, None)
        check_process(self, [sys.executable, test_program, "-r", "--out=Temp/utf8-2.svg",
                             "Temp/utf8-1.svg"],
                      "Results/empty", "Results/utf8-2.err",
                      None, "Temp/utf8-2.svg")


class TestViewBox(unittest.TestCase):
    def test_svg_noViewbox(self):
        """ Tests/viewBox-none.svg """
        test_svg_file(self, "viewBox-none.svg")

    def test_svg_ViewboxHeight(self):
        """ Tests/viewBox-height.svg """
        test_svg_file(self, "viewBox-height.svg")

    def test_svg_ViewboxWidth(self):
        """ Tests/viewBox-width.svg """
        test_svg_file(self, "viewBox-width.svg")

    def test_svg_ViewboxBoth(self):
        """ Tests/viewBox-both.svg """
        test_svg_file(self, "viewBox-both.svg")


def test_rfc_file(tester, fileName):
    """ Run the basic tests for a single input file """

    basename = os.path.basename(fileName)
    parse = XmlRfcParser("Tests/" + fileName, quiet=True, cache_path=None, no_network=True,
                         preserve_all_white=True)
    tree = parse.parse(remove_comments=False, remove_pis=True, strip_cdata=False)

    log.write_out = io.StringIO()
    log.write_err = log.write_out
    checkTree(tree.tree)

    returnValue = check_results(log.write_out, "Results/" + basename.replace(".xml", ".out"))
    tester.assertFalse(returnValue, "Output to console is different")

    result = io.StringIO(lxml.etree.tostring(tree.tree,
                                             xml_declaration=True,
                                             encoding='utf-8',
                                             pretty_print=True).decode('utf-8'))
    returnValue = check_results(result, "Results/" + basename)
    tester.assertFalse(returnValue, "Result from editing the tree is different")


def test_svg_file(tester, fileName):
    """ Run the basic tests for a single input file """

    basename = os.path.basename(fileName)
    parse = XmlRfcParser("Tests/" + fileName, quiet=True, cache_path=None, no_network=True,
                         preserve_all_white=True)
    tree = parse.parse(remove_comments=False, remove_pis=True, strip_cdata=False)

    log.write_out = io.StringIO()
    log.write_err = log.write_out
    checkTree(tree.tree)

    (result, errors) = tree.validate(rng_path=parse.default_rng_path.replace("rfc7991", "svg"))

    returnValue = check_results(log.write_out, "Results/" + basename.replace(".svg", ".out"))
    tester.assertFalse(returnValue, "Output to console is different")

    result = io.StringIO(lxml.etree.tostring(tree.tree,
                                             xml_declaration=True,
                                             encoding='utf-8',
                                             pretty_print=True).decode('utf-8'))
    returnValue = check_results(result, "Results/" + basename)
    tester.assertFalse(returnValue, "Result from editing the tree is different")
    tester.assertTrue(result, "Fails to validate againist the RNG")


def check_results(file1, file2Name):
    """  Compare two files and say what the differences are or even if there are
         any differences
    """

    with io.open(file2Name, 'r', encoding='utf-8') as f:
        lines2 = f.readlines()

    if os.name == 'nt' and (file2Name.endswith(".out") or file2Name.endswith(".err")):
        lines2 = [line.replace('Tests/', 'Tests\\').replace('Temp/', 'Temp\\') for line in lines2]

    if not file2Name.endswith(".out"):
        cwd = os.getcwd()
        if os.name == 'nt':
            cwd = cwd.replace('\\', '/')
        lines2 = [line.replace('$$CWD$$', cwd) for line in lines2]

    file1.seek(0)
    lines1 = file1.readlines()

    d = difflib.Differ()
    result = list(d.compare(lines1, lines2))

    hasError = False
    for line in result:
        if line[0:2] == '+ ' or line[0:2] == '- ':
            hasError = True
            break

    if hasError:
        print("".join(result))

    return hasError


def check_process(tester, args, stdoutFile, errFile, generatedFile, compareFile):
    """
    Execute a subprocess using args as the command line.
    if stdoutFile is not None, compare it to the stdout of the process
    if generatedFile and compareFile are not None, compare them to each other
    """

    if args[1][-4:] == '.exe':
        args = args[1:]
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdoutX, stderr) = p.communicate()
    p.wait()

    returnValue = True
    if stdoutFile is not None:
        with io.open(stdoutFile, 'r', encoding='utf-8') as f:
            lines2 = f.readlines()

        if six.PY2:
            lines1 = stdoutX.decode('utf-8').splitlines(True)
        else:
            lines1 = stdoutX.decode('utf-8').splitlines(True)

        if os.name == 'nt':
            lines2 = [line.replace('Tests/', 'Tests\\').replace('Temp/', 'Temp\\')
                      for line in lines2]
            lines1 = [line.replace('\r', '') for line in lines1]

        d = difflib.Differ()
        result = list(d.compare(lines1, lines2))

        hasError = False
        for line in result:
            if line[0:2] == '+ ' or line[0:2] == '- ':
                hasError = True
                break
        if hasError:
            print("stdout:")
            print(u"".join(result))
            returnValue = False

    if errFile is not None:
        with io.open(errFile, 'r', encoding='utf-8') as f:
            lines2 = f.readlines()

        if six.PY2:
            lines1 = stderr.decode('utf-8').splitlines(True)
        else:
            lines1 = stderr.decode('utf-8').splitlines(True)

        if os.name == 'nt':
            lines2 = [line.replace('Tests/', 'Tests\\').replace('Temp/', 'Temp\\')
                      for line in lines2]
            lines1 = [line.replace('\r', '') for line in lines1]

        d = difflib.Differ()
        result = list(d.compare(lines1, lines2))

        hasError = False
        for line in result:
            if line[0:2] == '+ ' or line[0:2] == '- ':
                hasError = True
                break
        if hasError:
            print("stderr")
            print("".join(result))
            returnValue = False

    if generatedFile is not None:
        with io.open(generatedFile, 'r', encoding='utf-8') as f:
            lines2 = f.readlines()

        with io.open(compareFile, 'r', encoding='utf-8') as f:
            lines1 = f.readlines()

        d = difflib.Differ()
        result = list(d.compare(lines1, lines2))

        hasError = False
        for line in result:
            if line[0:2] == '+ ' or line[0:2] == '- ':
                hasError = True
                break

        if hasError:
            print(generatedFile)
            print(u"".join(result))
            returnValue = False

    tester.assertTrue(returnValue, "Comparisons failed")


def clear_cache(parser):
    parser.delete_cache()


if __name__ == '__main__':
    if os.environ.get('RFCEDITOR_TEST'):
        test_program = "run.py"
    else:
        if os.name == 'nt':
            test_program += '.exe'
        test_program = which(test_program)
        if test_program is None:
            print("Failed to find the svgcheck for testing")
            test_program = "run.py"
    unittest.main(buffer=True)
