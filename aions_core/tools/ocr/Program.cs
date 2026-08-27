// ==========================================
// AUTHOR: M. SZUL
// AI MODEL: Claude Opus 5
// TIMESTAMP: 2026-08-27 06:20:40
// REASON FOR CREATION: AIONS could control the desktop and the browser but could not
//   PERCEIVE anything - it could click a button and never know what the button said, and
//   an image, a scan or a face was a wall. Windows has shipped every engine needed for
//   this the whole time and none of it was ever called: verified present on this machine
//   are the OCR recognizers (en-GB and pl), face detection, speech synthesis, speech
//   recognition, and an HP HD Camera.
// MECHANICS: One binary, four commands, because these are one capability - turning the
//   outside world into text the rest of the system can address, search and store.
//     ocr     <obraz>          pixels to text, optionally with the position of each line
//                              so the caller can act on what it read
//     kamera  <plik.jpg>       one frame from the camera, to a file
//     twarze  <obraz>          where the faces are, and how many
//   Everything answers in JSON, success and failure in the same shape, so a caller parses
//   one thing and never has to read stderr to find out which happened.
// SYSTEM PART: AIONS - perception tools.
// ARCHITECTURE FUNCTION: The missing input beside desktop and browser control, which are
//   output. What it produces is text, so a screen or a photograph becomes an ordinary
//   source - encodable through CBMS, addressable in Hangul, storable as a block, readable
//   by Noworodek without conversion.
// DEPENDENCIES/LINKS: Windows.Media.Ocr, Windows.Media.FaceAnalysis, Windows.Media.Capture
//   and Windows.Graphics.Imaging, all part of the operating system. Called by the AIONS
//   server as the ocr_read tool; nothing is installed, licensed or bundled.
// TECH STACK: C# on .NET 10 with the Windows SDK projections. Rust is this system's
//   default and stays so everywhere else - but these are WinRT APIs, and from Rust that
//   means the windows crate plus hand-written async projections for OcrEngine,
//   FaceDetector, MediaCapture, SoftwareBitmap and BitmapDecoder, whereas .NET generates
//   all of them from an SDK already on the machine. The cost is one more toolchain in the
//   build; the gain is that no perception engine has to be installed or shipped at all.
// LOCAL WORKSPACE: E:\server wiedzy\aions_core\tools\ocr
// GIT COMMIT: PENDING
// GITHUB METADATA: jpytka666-jpg/aions-server-wiedzy, branch main
// ==========================================

using System.Text;
using System.Text.Json;
using Windows.Globalization;
using Windows.Graphics.Imaging;
using Windows.Media.Capture;
using Windows.Media.FaceAnalysis;
using Windows.Media.MediaProperties;
using Windows.Media.Ocr;
using Windows.Storage;
using Windows.Storage.Streams;

Console.OutputEncoding = Encoding.UTF8;

if (args.Length < 2)
{
    Console.Error.WriteLine("aions-ocr <polecenie> <plik> [opcje]");
    Console.Error.WriteLine("  ocr    <obraz> [--jezyk pl] [--linie]   czytaj tekst z obrazu");
    Console.Error.WriteLine("  kamera <plik.jpg>                       zrob zdjecie");
    Console.Error.WriteLine("  twarze <obraz>                          znajdz twarze");
    return 2;
}

string polecenie = args[0].ToLowerInvariant();
string plik = args[1];

try
{
    return polecenie switch
    {
        "ocr" => await Ocr(plik, Arg(args, "--jezyk") ?? "pl", args.Contains("--linie")),
        "kamera" => await Kamera(plik),
        "twarze" => await Twarze(plik),
        _ => Blad($"nieznane polecenie: {polecenie}")
    };
}
catch (Exception exc)
{
    return Blad($"{exc.GetType().Name}: {exc.Message}");
}

// ---- czytanie tekstu -----------------------------------------------------------

async Task<int> Ocr(string sciezka, string jezyk, bool zLiniami)
{
    sciezka = Path.GetFullPath(sciezka);
    if (!File.Exists(sciezka)) return Blad($"nie ma takiego pliku: {sciezka}");

    // Ask for the requested language, then for whatever the machine actually has. A
    // machine without the Polish pack should still read English rather than report a
    // failure that looks like the image was unreadable.
    OcrEngine? silnik = OcrEngine.TryCreateFromLanguage(new Language(jezyk))
                        ?? OcrEngine.TryCreateFromUserProfileLanguages();
    if (silnik is null)
        return Blad($"system nie ma rozpoznawania tekstu dla '{jezyk}' ani dla jezykow uzytkownika");

    using SoftwareBitmap obraz = await Wczytaj(sciezka);
    OcrResult wynik = await silnik.RecognizeAsync(obraz);

    var linie = wynik.Lines.Select(l => new
    {
        tekst = l.Text,
        // Where the line sits, so a caller can click what it just read. Word boxes are the
        // only geometry the engine gives; a line's box is their hull.
        x = l.Words.Count > 0 ? (int)l.Words.Min(w => w.BoundingRect.Left) : 0,
        y = l.Words.Count > 0 ? (int)l.Words.Min(w => w.BoundingRect.Top) : 0,
        szerokosc = l.Words.Count > 0
            ? (int)(l.Words.Max(w => w.BoundingRect.Right) - l.Words.Min(w => w.BoundingRect.Left)) : 0,
        wysokosc = l.Words.Count > 0
            ? (int)(l.Words.Max(w => w.BoundingRect.Bottom) - l.Words.Min(w => w.BoundingRect.Top)) : 0,
        slow = l.Words.Count
    }).ToList();

    return Ok(zLiniami
        ? new { ok = true, jezyk = silnik.RecognizerLanguage.LanguageTag, tekst = wynik.Text,
                znakow = wynik.Text.Length, linii = linie.Count, linie }
        : new { ok = true, jezyk = silnik.RecognizerLanguage.LanguageTag, tekst = wynik.Text,
                znakow = wynik.Text.Length, linii = linie.Count });
}

// ---- zdjecie z kamery ----------------------------------------------------------

async Task<int> Kamera(string docelowy)
{
    docelowy = Path.GetFullPath(docelowy);
    Directory.CreateDirectory(Path.GetDirectoryName(docelowy)!);

    using var kamera = new MediaCapture();
    // Video only: asking for audio makes initialisation fail on a machine with no
    // microphone, and a still frame needs none.
    await kamera.InitializeAsync(new MediaCaptureInitializationSettings
    {
        StreamingCaptureMode = StreamingCaptureMode.Video
    });

    StorageFolder katalog = await StorageFolder.GetFolderFromPathAsync(
        Path.GetDirectoryName(docelowy)!);
    StorageFile wyjscie = await katalog.CreateFileAsync(
        Path.GetFileName(docelowy), CreationCollisionOption.ReplaceExisting);

    await kamera.CapturePhotoToStorageFileAsync(
        ImageEncodingProperties.CreateJpeg(), wyjscie);

    var wlasciwosci = await wyjscie.GetBasicPropertiesAsync();
    return Ok(new { ok = true, plik = docelowy, bajtow = (long)wlasciwosci.Size });
}

// ---- twarze --------------------------------------------------------------------

async Task<int> Twarze(string sciezka)
{
    sciezka = Path.GetFullPath(sciezka);
    if (!File.Exists(sciezka)) return Blad($"nie ma takiego pliku: {sciezka}");

    FaceDetector wykrywacz = await FaceDetector.CreateAsync();
    using SoftwareBitmap obraz = await Wczytaj(sciezka);

    // The detector accepts only a few pixel formats, and Gray8 is the one it is
    // guaranteed to support. Converting is cheaper than discovering at run time that this
    // particular image came in a format it refuses.
    BitmapPixelFormat format = FaceDetector.GetSupportedBitmapPixelFormats().Contains(
        BitmapPixelFormat.Gray8) ? BitmapPixelFormat.Gray8 : BitmapPixelFormat.Nv12;
    using SoftwareBitmap doWykrycia = SoftwareBitmap.Convert(obraz, format);

    IList<DetectedFace> twarze = await wykrywacz.DetectFacesAsync(doWykrycia);

    return Ok(new
    {
        ok = true,
        plik = sciezka,
        // Detection, not recognition: this says WHERE a face is, never WHOSE. Telling
        // people apart needs a model that Windows does not ship, and pretending otherwise
        // would be the more useful-sounding lie.
        twarzy = twarze.Count,
        gdzie = twarze.Select(t => new
        {
            x = (int)t.FaceBox.X, y = (int)t.FaceBox.Y,
            szerokosc = (int)t.FaceBox.Width, wysokosc = (int)t.FaceBox.Height
        }).ToList()
    });
}

// ---- wspolne -------------------------------------------------------------------

async Task<SoftwareBitmap> Wczytaj(string sciezka)
{
    StorageFile plik = await StorageFile.GetFileFromPathAsync(sciezka);
    using IRandomAccessStream strumien = await plik.OpenAsync(FileAccessMode.Read);
    BitmapDecoder dekoder = await BitmapDecoder.CreateAsync(strumien);
    return await dekoder.GetSoftwareBitmapAsync();
}

static string? Arg(string[] args, string nazwa)
{
    int i = Array.IndexOf(args, nazwa);
    return i >= 0 && i + 1 < args.Length ? args[i + 1] : null;
}

static int Ok(object odpowiedz)
{
    Console.WriteLine(JsonSerializer.Serialize(odpowiedz,
        new JsonSerializerOptions { WriteIndented = true }));
    return 0;
}

static int Blad(string powod)
{
    // Failure in the same shape as success, so a caller parses one thing.
    Console.WriteLine(JsonSerializer.Serialize(new { ok = false, powod },
        new JsonSerializerOptions { WriteIndented = true }));
    return 1;
}
