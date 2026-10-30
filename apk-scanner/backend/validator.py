"""Validasi file APK sebelum dianalisis. File berasal dari luar dan tidak tepercaya."""
import zipfile

MAX_BYTES = 150 * 1024 * 1024
MAX_UNCOMPRESSED = 500 * 1024 * 1024  # dari central directory ZIP, tanpa ekstraksi: menolak zip bomb


class InvalidApk(ValueError):
    pass


def validate(path, size):
    """Lempar InvalidApk bila file bukan APK yang bisa dianalisis."""
    if size > MAX_BYTES:
        raise InvalidApk("file melebihi 150 MB")
    if not zipfile.is_zipfile(path):
        raise InvalidApk("bukan file APK (bukan arsip ZIP)")
    try:
        with zipfile.ZipFile(path) as z:
            infos = z.infolist()
    except (zipfile.BadZipFile, OSError) as exc:
        raise InvalidApk(f"arsip ZIP rusak: {exc}")
    names = {i.filename for i in infos}
    if "AndroidManifest.xml" not in names:
        raise InvalidApk("tidak ada AndroidManifest.xml (bukan APK, atau split APK .apks/.xapk yang belum didukung)")
    if "classes.dex" not in names:
        raise InvalidApk("tidak ada classes.dex")
    if sum(i.file_size for i in infos) > MAX_UNCOMPRESSED:
        raise InvalidApk("ukuran terekstrak melebihi 500 MB (kemungkinan zip bomb)")
