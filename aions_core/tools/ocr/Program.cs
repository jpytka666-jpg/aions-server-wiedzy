// ==========================================
// AUTHOR: M. SZUL
// AI MODEL: Claude Opus 5
// TIMESTAMP: 2026-08-27 06:05:20
// REASON FOR CREATION: AIONS can control the desktop and the browser but cannot READ a
//   screen - it can click a button and never know what the button said. An image, a scan,
//   a PDF page or a screenshot is a wall. Windows has shipped an OCR engine this whole
//   time, with the Polish recognizer already installed and never called: measured,
//   AvailableRecognizerLanguages returns en-GB and pl.
// MECHANICS: Takes an image path, returns the recognised text - plain, or with the
//   position of every line when the caller needs to know WHERE on the screen something
//   was. Language defaults to Polish and falls back to whatever the machine has rather
//   than failing, because a machine with only English installed should still read English.
//   Writes nothing and touches nothing: it is a reader.
// SYSTEM PART: AIONS - perception tools.
// ARCHITECTURE FUNCTION: Turns pixels into text so the rest of the system can treat a
//   screen like any other source - searchable through CBMS, addressable, storable as a
//   block. It is the missing input next to desktop and browser control, which are output.
// DEPENDENCIES/LINKS: Windows.Media.Ocr and Windows.Graphics.Imaging, both part of the
//   operating system; nothing is installed or bundled. Called by the AIONS server as a
//   tool; output is JSON on stdout.
// TECH STACK: C# on .NET 10 with the Windows SDK projections. Rust is this system's
//   default and stays so everywhere else - but the OCR engine is a WinRT API, and from
//   Rust that means the windows crate plus hand-written async projections for OcrEngine,
//   SoftwareBitmap and BitmapDecoder, whereas .NET generates them from the SDK that is
//   already on the machine. The cost is one more toolchain in the build; the gain is that
//   no OCR engine has to be installed, licensed or shipped at all.
// LOCAL WORKSPACE: E:\server wiedzy\aions_core\tools\ocr
// GIT COMMIT: PENDING
// GITHUB METADATA: jpytka666-jpg/aions-server-wiedzy, branch main
// ==========================================

using System.Globalization;
using System.Text;
using System.Text.Json;
using Windows.Globalization;
using Windows.Graphics.Imaging;
using Windows.Media.Ocr;
using Windows.Storage;
using Windows.Storage.Streams;

Console.OutputEncoding = Encoding.UTF8;

if (args.Length < 1)
{
    Console.Error.WriteLine("aions-ocr <plik-obrazu> [--jezyk pl] [--linie]");
    Console.Error.WriteLine("  --linie  dopisuje polozenie kazdej linii na obrazie");
    return 2;
}

string sciezka = Path.GetFullPath(args[0]);
string jezyk = Arg(args, "--jezyk") ?? "pl";
bool zLiniami = args.Contains("--linie");

if (!File.Exists(sciezka))
{
    return Blad($"nie ma takiego pliku: {sciezka}");
}

try
{
    // Ask for the requested language, then for whatever the machine actually has. A
    // machine without the Polish pack should still read English rather than report a
    // failure that looks like the image was unreadable.
    OcrEngine? silnik = OcrEngine.TryCreateFromLanguage(new Language(jezyk))
                        ?? OcrEngine.TryCreateFromUserProfileLanguages();
    if (silnik is null)
    {
        return Blad($"system nie ma zadnego rozpoznawania tekstu dla '{jezyk}' " +
                    "ani dla jezykow uzytkownika");
    }

    StorageFile plik = await StorageFile.GetFileFromPathAsync(sciezka);
    using IRandomAccessStream strumien = await plik.OpenAsync(FileAccessMode.Read);
    BitmapDecoder dekoder = await BitmapDecoder.CreateAsync(strumien);
    using SoftwareBitmap obraz = await dekoder.GetSoftwareBitmapAsync();

    OcrResult wynik = await silnik.RecognizeAsync(obraz);

    var linie = wynik.Lines.Select(l => new
    {
        tekst = l.Text,
        // Position of the line on the image, so a caller can click what it just read.
        // Word boxes are the only geometry the engine gives; a line's box is their hull.
        x = l.Words.Count > 0 ? (int)l.Words.Min(w => w.BoundingRect.Left) : 0,
        y = l.Words.Count > 0 ? (int)l.Words.Min(w => w.BoundingRect.Top) : 0,
        szerokosc = l.Words.Count > 0
            ? (int)(l.Words.Max(w => w.BoundingRect.Right) - l.Words.Min(w => w.BoundingRect.Left))
            : 0,
        wysokosc = l.Words.Count > 0
            ? (int)(l.Words.Max(w => w.BoundingRect.Bottom) - l.Words.Min(w => w.BoundingRect.Top))
            : 0,
        slow = l.Words.Count
    }).ToList();

    object odpowiedz = zLiniami
        ? new
        {
            ok = true,
            jezyk = silnik.RecognizerLanguage.LanguageTag,
            tekst = wynik.Text,
            znakow = wynik.Text.Length,
            linii = linie.Count,
            linie
        }
        : new
        {
            ok = true,
            jezyk = silnik.RecognizerLanguage.LanguageTag,
            tekst = wynik.Text,
            znakow = wynik.Text.Length,
            linii = linie.Count
        };

    Console.WriteLine(JsonSerializer.Serialize(odpowiedz,
        new JsonSerializerOptions { WriteIndented = true }));
    return 0;
}
catch (Exception exc)
{
    return Blad($"{exc.GetType().Name}: {exc.Message}");
}

static string? Arg(string[] args, string nazwa)
{
    int i = Array.IndexOf(args, nazwa);
    return i >= 0 && i + 1 < args.Length ? args[i + 1] : null;
}

static int Blad(string powod)
{
    // Errors go out in the same shape as success, so a caller parses one thing.
    Console.WriteLine(JsonSerializer.Serialize(new { ok = false, powod },
        new JsonSerializerOptions { WriteIndented = true }));
    return 1;
}
