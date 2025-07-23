"""File processing service for chat application."""

import mimetypes
from pathlib import Path
from typing import Any


class FileProcessor:
    """Service for processing uploaded files."""

    ALLOWED_EXTENSIONS = {
        'text': {'.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', '.yaml', '.yml'},
        'image': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'},
        'document': {'.pdf', '.doc', '.docx'},
        'data': {'.csv', '.tsv', '.xlsx'}
    }

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    @classmethod
    def is_allowed_file(cls, filename: str) -> bool:
        """Check if file extension is allowed."""
        ext = Path(filename).suffix.lower()
        return any(ext in extensions for extensions in cls.ALLOWED_EXTENSIONS.values())

    @classmethod
    def get_file_category(cls, filename: str) -> str:
        """Get file category based on extension."""
        ext = Path(filename).suffix.lower()
        for category, extensions in cls.ALLOWED_EXTENSIONS.items():
            if ext in extensions:
                return category
        return 'unknown'

    @classmethod
    def process_file(cls, file_content: bytes, filename: str) -> dict[str, Any]:
        """Process uploaded file and extract content."""
        try:
            if len(file_content) > cls.MAX_FILE_SIZE:
                return {
                    'success': False,
                    'error': f'File too large. Maximum size is {cls.MAX_FILE_SIZE // (1024*1024)}MB'
                }

            if not cls.is_allowed_file(filename):
                return {
                    'success': False,
                    'error': f'File type not supported. Allowed extensions: {cls._get_allowed_extensions_string()}'
                }

            category = cls.get_file_category(filename)

            if category == 'text':
                return cls._process_text_file(file_content, filename)
            elif category == 'image':
                return cls._process_image_file(file_content, filename)
            elif category == 'document':
                return cls._process_document_file(file_content, filename)
            elif category == 'data':
                return cls._process_data_file(file_content, filename)
            else:
                return {
                    'success': False,
                    'error': 'Unsupported file type'
                }

        except Exception as e:
            return {
                'success': False,
                'error': f'Error processing file: {str(e)}'
            }

    @classmethod
    def _process_text_file(cls, file_content: bytes, filename: str) -> dict[str, Any]:
        """Process text files."""
        try:
            # Try different encodings
            for encoding in ['utf-8', 'utf-16', 'latin1', 'cp1252']:
                try:
                    content = file_content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                return {
                    'success': False,
                    'error': 'Could not decode file content'
                }

            lines = content.split('\n')
            word_count = len(content.split())
            char_count = len(content)

            return {
                'success': True,
                'category': 'text',
                'filename': filename,
                'content': content,
                'metadata': {
                    'lines': len(lines),
                    'words': word_count,
                    'characters': char_count,
                    'encoding': encoding,
                    'size_bytes': len(file_content)
                },
                'summary': f"Text file with {len(lines)} lines, {word_count} words"
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Error reading text file: {str(e)}'
            }

    @classmethod
    def _process_image_file(cls, file_content: bytes, filename: str) -> dict[str, Any]:
        """Process image files."""
        try:
            # For now, just return basic info
            # In production, you might use PIL/Pillow to extract image metadata

            return {
                'success': True,
                'category': 'image',
                'filename': filename,
                'content': f"Image file: {filename}",
                'metadata': {
                    'size_bytes': len(file_content),
                    'mime_type': mimetypes.guess_type(filename)[0]
                },
                'summary': f"Image file ({len(file_content)} bytes)"
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Error processing image: {str(e)}'
            }

    @classmethod
    def _process_document_file(cls, file_content: bytes, filename: str) -> dict[str, Any]:
        """Process document files (PDF, Word, etc.)."""
        try:
            # For now, just return basic info
            # In production, you might use libraries like PyPDF2, python-docx, etc.

            return {
                'success': True,
                'category': 'document',
                'filename': filename,
                'content': f"Document file: {filename} (content extraction not implemented)",
                'metadata': {
                    'size_bytes': len(file_content),
                    'mime_type': mimetypes.guess_type(filename)[0]
                },
                'summary': f"Document file ({len(file_content)} bytes)"
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Error processing document: {str(e)}'
            }

    @classmethod
    def _process_data_file(cls, file_content: bytes, filename: str) -> dict[str, Any]:
        """Process data files (CSV, Excel, etc.)."""
        try:
            ext = Path(filename).suffix.lower()

            if ext == '.csv':
                content = file_content.decode('utf-8')
                lines = content.split('\n')
                # Simple CSV analysis
                if lines:
                    header = lines[0].split(',')
                    data_rows = len([line for line in lines[1:] if line.strip()])

                    return {
                        'success': True,
                        'category': 'data',
                        'filename': filename,
                        'content': f"CSV data with {len(header)} columns and {data_rows} rows:\n\nColumns: {', '.join(header)}\n\nFirst few rows:\n" + '\n'.join(lines[:5]),
                        'metadata': {
                            'columns': len(header),
                            'rows': data_rows,
                            'size_bytes': len(file_content),
                            'column_names': header
                        },
                        'summary': f"CSV file with {len(header)} columns and {data_rows} rows"
                    }

            # Fallback for other data formats
            return {
                'success': True,
                'category': 'data',
                'filename': filename,
                'content': f"Data file: {filename} (detailed parsing not implemented for {ext})",
                'metadata': {
                    'size_bytes': len(file_content),
                    'mime_type': mimetypes.guess_type(filename)[0]
                },
                'summary': f"Data file ({len(file_content)} bytes)"
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Error processing data file: {str(e)}'
            }

    @classmethod
    def _get_allowed_extensions_string(cls) -> str:
        """Get formatted string of allowed extensions."""
        all_extensions = set()
        for extensions in cls.ALLOWED_EXTENSIONS.values():
            all_extensions.update(extensions)
        return ', '.join(sorted(all_extensions))
