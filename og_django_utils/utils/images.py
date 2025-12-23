import os
import tempfile

from filebrowser.base import FileObject
from filebrowser.settings import VERSION_QUALITY, DEFAULT_PERMISSIONS
from filebrowser.utils import process_image
from PIL import Image

from django.core.files import File


class FileObjectExtended(FileObject):

    def is_webm(self):
        base, ext = os.path.splitext(self.path)
        return ext == ".webm"

    def version_generate(self, version_suffix, extra_options=None, webp=False):
        "Generate a version"  # FIXME: version_generate for version?
        path = self.path
        options = self._get_options(version_suffix, extra_options)

        version_path = self.version_path(version_suffix, extra_options)
        filename, ext = os.path.splitext(version_path)
        webp_path = '{}.webp'.format(filename)
        if not ext:
            return FileObject(version_path, site=self.site)

        if not self.site.storage.isfile(version_path):
            version_path = self._generate_version(version_path, options)
        elif hasattr(self.site.storage, 'get_modified_time'):
            if self.site.storage.get_modified_time(path) > self.site.storage.get_modified_time(version_path):
                version_path = self._generate_version(version_path, options)
        elif self.site.storage.modified_time(path) > self.site.storage.modified_time(version_path):
            version_path = self._generate_version(version_path, options)

        if not self.site.storage.isfile(webp_path):
            self._generate_version(webp_path, options, webp_only=True)
        elif hasattr(self.site.storage, 'get_modified_time'):
            if self.site.storage.get_modified_time(path) > self.site.storage.get_modified_time(webp_path):
                version_path = self._generate_version(webp_path, options, webp_only=True)
        elif self.site.storage.modified_time(path) > self.site.storage.modified_time(webp_path):
            version_path = self._generate_version(webp_path, options, webp_only=True)

        if webp:
            version_path = webp_path

        return FileObject(version_path, site=self.site)

    def _generate_webp_version(self, webp_path, im):
        webp_temp = File(tempfile.NamedTemporaryFile())
        im.save(webp_temp, 'WEBP')
        self.site.storage.save(webp_path, webp_temp)

    def get_gif_frame(self):
        base, ext = os.path.splitext(self.name)
        frame_path = "{}_frame.jpg".format(base)
        if not self.site.storage.isfile(frame_path):
            try:
                f = self.site.storage.open(self.path)
            except IOError:
                raise ValueError('path')
            image = Image.open(f)
            frame_temp = File(tempfile.NamedTemporaryFile())
            image.convert('RGB').save(frame_temp, 'JPEG')
            self.site.storage.save(frame_path, frame_temp)
            image.close()
        return FileObjectExtended(frame_path, site=self.site)

    def _generate_version(self, version_path, options, webp_only=False):
        """
        Generate Version for an Image.
        value has to be a path relative to the storage location.
        """

        tmpfile = File(tempfile.NamedTemporaryFile())

        try:
            f = self.site.storage.open(self.path)
        except IOError:
            return ""
        im = Image.open(f)
        version_dir, version_basename = os.path.split(version_path)
        root, ext = os.path.splitext(version_basename)
        version = process_image(im, options)
        filename, ext = os.path.splitext(version_path)
        webp_path = '{}.webp'.format(filename)
        self._generate_webp_version(webp_path, version)
        if webp_only:
            return webp_path
        if not version:
            version = im
        if 'methods' in options:
            for m in options['methods']:
                if callable(m):
                    version = m(version)

        # IF need Convert RGB
        if ext in [".jpg", ".jpeg"] and version.mode not in ("L", "RGB"):
            version = version.convert("RGB")

        # save version
        try:
            version.save(tmpfile, format=Image.EXTENSION[ext.lower()], quality=VERSION_QUALITY, optimize=(os.path.splitext(version_path)[1] != '.gif'))
        except IOError:
            version.save(tmpfile, format=Image.EXTENSION[ext.lower()], quality=VERSION_QUALITY)
        # remove old version, if any
        if version_path != self.site.storage.get_available_name(version_path):
            self.site.storage.delete(version_path)
        self.site.storage.save(version_path, tmpfile)
        # set permissions
        if DEFAULT_PERMISSIONS is not None:
            os.chmod(self.site.storage.path(version_path), DEFAULT_PERMISSIONS)
        return version_path
