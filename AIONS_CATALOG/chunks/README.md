# 📦 CHUNKS - Fragmenty wiedzy CBMS

## Lokalizacje chunków

### 1. ContextVault (GŁÓWNE)
- **Ilość**: 505 chunków
- **Ścieżka**: `C:\Users\User\ContextVault\memory\chunks\`
- **Format**: JSON (K*.json)

### 2. AIONS V3 (Aktywny serwer)
- **Ilość**: 521 chunków
- **Ścieżka**: `C:\Users\User\OneDrive - Global Banking School\Desktop\AIONS_CBMS_RELEASE_V3\memory\chunks\`

### 3. AIONS Versions (V0-V2, VANILA)
- **Ścieżka base**: `E:\AI_WORKSPACE\MASTER_CLEAN\AIONS_CORE\AIONS_V10\`
- **Wersje**: AIONS_CBMS_RELEASE_V0, V1, V2, V3, VANILA

## Format chunka

```json
{
  "id": "K7E56D0E78FC3",
  "concept": "general",
  "content": "Treść wiedzy...",
  "references": ["K...", "K..."],
  "access_count": 0,
  "metadata": {}
}
```

## Adresowanie K[hex]
- Format: K + 12-13 znaków hex
- Przestrzeń: 16^13 = 1.15 × 10^15

## Typy chunków
- Knowledge (wiedza domenowa)
- Thinking Pattern (wzorce myślenia)
- Meta (referencje)
- Bootstrap (inicjalizacja)
