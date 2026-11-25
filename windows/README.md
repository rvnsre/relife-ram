# Windows-dan USB-siz ReLife açılışı

ReLife Windows Boot Setup mövcud, ayrı FAT32 bölməsinə Extreme Lite canlı
sistemini hazırlayır. EFI faylı imzasızdır və 64-bit UEFI-nin **Boot from File**
seçimi tələb olunur. Windows və Windows-un EFI sistem bölməsindən ayrı olan,
sürücü hərfi təyin edilmiş FAT32 bölməsi seç. Bu bölmədə ən azı payload ZIP-in
ölçüsü qədər boş yer, Windows-un müvəqqəti qovluğunda da eyni həcmdə boş yer
lazımdır. Bölmənin yaradılması bu alətdən kənardır.

1. Eyni buraxılışdan `ReLife-Windows-Boot-Setup.exe`,
   `ReLife-Windows-UEFI-Payload.zip` və `SHA256SUMS` fayllarını götür.
2. PowerShell-də ZIP-in SHA-256 göstəricisini yoxla. `R:` nümunəsini öz
   bölmənin hərfi ilə və `DIGEST` yerini `SHA256SUMS` faylındakı ZIP-ə aid
   64 simvolluq göstərici ilə əvəz et.

   ```powershell
   Get-FileHash .\ReLife-Windows-UEFI-Payload.zip -Algorithm SHA256
   .\ReLife-Windows-Boot-Setup.exe -volume R: -payload .\ReLife-Windows-UEFI-Payload.zip -sha256 DIGEST -confirm
   ```

3. UEFI-də **Boot from File** seçimini aç, həmin FAT32 bölməsindən
   `\EFI\ReLife\ReLife.efi` faylını seç. ReLife əməliyyat sistemini RAM-a
   köçürür. Sessiyadan çıxanda saxlanmalı faylları ayrıca yaddaşa ixrac et.
4. Windows-a qayıtmaq üçün normal yenidən başladıb **Windows Boot Manager**
   seç. Quraşdırılmış faylları Windows-dan çıxarmaq üçün eyni bölməni göstər.

   ```powershell
   .\ReLife-Windows-Boot-Setup.exe -volume R: -remove -confirm
   ```

Alət disk bölmələrini yaratmır və formatlamır. Açılış sırasını, BCD-ni və
Windows Boot Manager-i dəyişdirmir. Secure Boot dəstəyi bu buraxılışa daxil deyil.
Windows sazlamalarını dəyişdirməzdən əvvəl BitLocker bərpa açarının harada
saxlandığını yoxla. UEFI-də fayldan açılış mümkün deyilsə, hibrid ISO istifadə et.
