# NonicaTab AI Connector - Pełna Analiza Architektury MCP

**Data analizy:** 2025-12-01
**Wersja:** NonicaTab FREE 1.4
**Lokalizacja:** C:\NONICA\

---

## 1. ARCHITEKTURA GŁÓWNA

### Komponenty systemu:
```
Claude Desktop ←→ RevitMCPConnection.exe ←→ Core_NonicaTabFREE_MCP.dll ←→ Revit API
     (MCP Client)      (MCP Server .NET 8)        (Plugin Revit)         (Revit 2022-2026)
```

### Kluczowe pliki:
| Plik | Ścieżka | Funkcja |
|------|---------|---------|
| RevitMCPConnection.exe | C:\NONICA\OtherFiles\System\Core\net8.0-windows\ | Serwer MCP (stdio) |
| Core_NonicaTabFREE_MCP.dll | C:\NONICA\OtherFiles\System\Core\net8.0-windows\ | Plugin Revit z narzędziami |
| Core_LoaderNonicaTabFREE.dll | C:\NONICA\OtherFiles\System\Core\net8.0-windows\ | Loader pluginu |
| ToolbarSettings.xml | C:\NONICA\OtherFiles\System\ | Konfiguracja 12 przycisków |

---

## 2. KONFIGURACJA MCP

### Claude Desktop Config:
```json
{
  "mcpServers": {
    "Revit": {
      "type": "stdio",
      "command": "C:\\NONICA\\OtherFiles\\System\\Core\\net8.0-windows\\RevitMCPConnection.exe",
      "args": [],
      "timeout": 15000
    }
  }
}
```

### Plugin Revit (.addin):
```xml
<RevitAddIns>
  <AddIn Type="Application">
    <n>NonicaTab FREE</n>
    <Assembly>"C:\NONICA\OtherFiles\System\Core\net8.0-windows\Core_NonicaTabFREE_MCP.dll"</Assembly>
    <AddInId>604b1552-f743-4959-8516-c256d1993174</AddInId>
    <FullClassName>Core_NonicaTabFREE_MCP.App</FullClassName>
    <VendorId>Nonica</VendorId>
  </AddIn>
</RevitAddIns>
```

---

## 3. NARZĘDZIA MCP (37 FREE / 50+ PRO)

### FREE TIER - Read + Analyze (37 tools):

#### Pobieranie danych modelu:
- `get_active_view_in_revit` - aktywny widok
- `get_user_selection_in_revit` - zaznaczenie użytkownika
- `get_model_categories` - kategorie w modelu
- `get_category_by_keyword` - wyszukiwanie kategorii
- `get_elements_by_category` - elementy po kategorii
- `get_all_elements_shown_in_view` - elementy w widoku

#### Parametry i właściwości:
- `get_parameters_from_elementid` - parametry elementu
- `get_parameter_value_for_element_ids` - wartości parametrów (bulk)
- `get_all_additional_properties_from_elementid` - dodatkowe właściwości
- `get_additional_property_for_all_elementids` - właściwości (bulk)

#### Rodziny i typy:
- `get_all_used_families_in_model` - rodziny w modelu
- `get_all_used_families_of_category` - rodziny kategorii
- `get_all_used_types_of_families` - typy rodzin
- `get_all_elements_of_specific_families` - elementy rodzin
- `get_all_elementids_for_specific_type_ids` - elementy typów
- `get_element_types_for_elementids` - typy elementów

#### Geometria i lokalizacja:
- `get_boundingboxes_for_element_ids` - bounding boxy
- `get_location_for_element_ids` - lokalizacje
- `get_boundary_lines` - linie graniczne (ściany/podłogi/pomieszczenia)
- `get_host_id_for_element_ids` - hosty elementów

#### Widoki i arkusze:
- `get_viewports_and_schedules_on_sheets` - viewporty na arkuszach
- `get_schedules_info_and_columns` - info o zestawieniach
- `get_graphic_filters_applied_to_views` - filtry graficzne
- `get_graphic_overrides_view_filters` - nadpisania filtrów
- `get_graphic_overrides_for_element_ids_in_view` - nadpisania elementów

#### Materiały i warstwy:
- `get_material_layers_from_types` - warstwy materiałów

#### Worksharing:
- `get_all_workset_information` - informacje o worksetach
- `get_worksets_from_elementids` - worksety elementów
- `get_worksharing_information_for_element_ids` - info worksharing

#### Ostrzeżenia i klasy:
- `get_all_warnings_in_the_model` - ostrzeżenia modelu
- `get_object_classes_from_elementids` - klasy obiektów
- `get_categories_from_elementids` - kategorie elementów

#### Filtry i dokumenty:
- `get_if_elements_pass_filter` - test filtra
- `get_document_switched` - przełączanie dokumentów (linki)

#### Narzędzia tworzenia (eksploracja):
- `create_tool_names_explorer` - lista narzędzi
- `create_tool_arguments_explorer` - argumenty narzędzi

---

### PRO TIER - Edit + Document (+13 tools):

#### Modyfikacja:
- `set_parameter_value_for_elements` - ustawianie parametrów
- `set_additional_property_for_all_elements` - ustawianie właściwości
- `set_user_selection_in_revit` - ustawianie zaznaczenia
- `set_isolated_elements_in_view` - izolowanie elementów
- `set_graphic_overrides_for_elements_in_view` - kolorowanie elementów

#### Transformacje:
- `set_movement_for_elements` - przesuwanie
- `set_rotation_for_elements` - obracanie
- `set_copy_elements` - kopiowanie/duplikowanie

#### Usuwanie:
- `set_delete_elements` - usuwanie elementów

#### Widoki i filtry:
- `set_copy_view_filters` - kopiowanie filtrów
- `set_revisions_on_sheets` - rewizje na arkuszach

#### Tworzenie (invoker):
- `create_tools_invoker` - wywoływanie narzędzi tworzenia

---

## 4. ZALEŻNOŚCI (.NET 8.0)

```json
{
  "DotNetZip": "1.16.0",
  "LiveCharts.NetCore": "0.9.8",
  "LiveCharts.Wpf.Core": "0.9.8",
  "Magick.NET-Q16-AnyCPU": "13.6.0",
  "Newtonsoft.Json": "13.0.3",
  "System.Drawing.Common": "8.0.3",
  "System.Management": "8.0.0",
  "gong-wpf-dragdrop": "3.2.1"
}
```

---

## 5. STRUKTURA KATALOGÓW

```
C:\NONICA\
├── Button1-12/           # Konfiguracje 12 przycisków toolbara
├── OtherFiles/
│   ├── System/
│   │   ├── Core/
│   │   │   └── net8.0-windows/
│   │   │       ├── RevitMCPConnection.exe    # MCP Server
│   │   │       ├── Core_NonicaTabFREE_MCP.dll # Plugin główny
│   │   │       ├── Core_LoaderNonicaTabFREE.dll
│   │   │       ├── IronPython/               # Środowisko Dynamo
│   │   │       │   └── DynamoIronPython2.7/
│   │   │       └── [zależności .dll]
│   │   ├── ToolbarSettings.xml               # Config przycisków
│   │   ├── TheBestOfTheBest.ntab            # Preset toolbara
│   │   └── [ikony, rodziny .rfa]
│   ├── Temp/
│   └── UserIcons/
```

---

## 6. KOMUNIKACJA MCP

### Protokół:
- **Transport:** stdio (stdin/stdout)
- **Format:** JSON-RPC 2.0
- **Timeout:** 15000ms (konfigurowalny)

### Flow:
1. Claude Desktop uruchamia RevitMCPConnection.exe jako subprocess
2. Komunikacja przez stdin/stdout (JSON)
3. RevitMCPConnection.exe komunikuje się z pluginem w Revit
4. Plugin wykonuje operacje przez Revit API
5. Wyniki wracają tą samą ścieżką

### Wymagania:
- Okno AI Connector w Revit musi być otwarte
- Toggle "Enable Connection" musi być włączony
- Claude Desktop musi być zrestartowany po pierwszym włączeniu

---

## 7. TROUBLESHOOTING

### "Access to the path is denied":
- Uruchom Claude Desktop jako Administrator
- Sprawdź czy antywirus nie blokuje

### "Request timeout":
1. Sprawdź czy AI Connector jest włączony w Revit
2. Wyłącz i włącz toggle "Enable Connection"
3. Zrestartuj Claude Desktop (Quit z system tray)
4. Sprawdź proces: `tasklist | findstr RevitMCP`

### Brak połączenia:
- Config musi być w: `%APPDATA%\Claude\claude_desktop_config.json`
- Jeśli Claude zainstalowane jako Admin, ręcznie dodaj config

---

## 8. PORÓWNANIE Z OPEN-SOURCE

| Cecha | NonicaTab FREE | revit-mcp-python |
|-------|----------------|------------------|
| Język | C# (.NET 8) | Python |
| Transport | stdio | HTTP (pyRevit Routes) |
| Port | N/A | 48884 |
| Narzędzia | 37 | ~15 |
| Wymagania | NonicaTab plugin | pyRevit |
| Licencja | Proprietary | MIT |
| Edycja | PRO only ($50/rok) | Tak |

---

## 9. MOŻLIWOŚCI ROZBUDOWY

### Opcja A: Użyć NonicaTab jako jest
- 37 narzędzi READ w wersji FREE
- PRO za $50/rok dodaje EDIT

### Opcja B: revit-mcp-python (open-source)
- Wymaga pyRevit
- Pełna kontrola nad kodem
- HTTP REST API na porcie 48884

### Opcja C: Własny plugin Revit + MCP Server
- Napisać własny plugin C#
- Własny serwer MCP w Python/Node
- Komunikacja przez socket/named pipe

---

## 10. NOTATKI TECHNICZNE

- IronPython 2.7 używany do Dynamo scripts
- Magick.NET do przetwarzania obrazów
- LiveCharts do wykresów w UI
- Stripe.NET - system płatności PRO
- System obsługuje Revit 2022-2026
- Plugin ładowany przez Core_LoaderNonicaTabFREE.dll

---

*Dokument wygenerowany automatycznie przez Claude AI podczas analizy struktury NonicaTab.*
