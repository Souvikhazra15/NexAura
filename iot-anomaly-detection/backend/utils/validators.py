"""
File validation utilities for CSV upload
"""
import os
from config.settings import MAX_FILE_SIZE_MB, ALLOWED_EXTENSIONS
import pandas as pd


class ValidationError(Exception):
    """Custom validation error"""
    pass


def validate_file_extension(filename: str) -> bool:
    """
    Validate that the file has allowed extension.
    
    Args:
        filename: Name of the file
        
    Returns:
        bool: True if valid extension
        
    Raises:
        ValidationError: If invalid extension
    """
    if '.' not in filename:
        raise ValidationError("File must have an extension")
    
    ext = filename.rsplit('.', 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(f"Only {ALLOWED_EXTENSIONS} files allowed. Got .{ext}")
    
    return True


def validate_file_size(file_path: str) -> bool:
    """
    Validate file size doesn't exceed limit.
    
    Args:
        file_path: Path to the file
        
    Returns:
        bool: True if valid size
        
    Raises:
        ValidationError: If file too large
    """
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        raise ValidationError(f"File too large. Max {MAX_FILE_SIZE_MB}MB, got {file_size_mb:.1f}MB")
    
    return True


def validate_csv_content(file_path: str) -> tuple[pd.DataFrame, str]:
    """
    Validate CSV content and return dataframe.
    
    Args:
        file_path: Path to CSV file
        
    Returns:
        tuple: (DataFrame, error_message)
        
    Raises:
        ValidationError: If CSV invalid
    """
    try:
        df = pd.read_csv(file_path)
    except pd.errors.ParserError as e:
        raise ValidationError(f"Invalid CSV format: {str(e)}")
    except Exception as e:
        raise ValidationError(f"Error reading CSV: {str(e)}")
    
    # Check if empty
    if df.empty:
        raise ValidationError("CSV file is empty")
    
    # Check minimum rows
    if len(df) < 10:
        raise ValidationError(f"CSV must have at least 10 rows. Got {len(df)}")
    
    # Check for numeric columns
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    if len(numeric_cols) < 2:
        raise ValidationError(f"CSV must have at least 2 numeric columns. Got {len(numeric_cols)}")
    
    return df, None


def validate_all(filename: str, file_path: str) -> tuple[bool, str, pd.DataFrame]:
    """
    Run all validation checks.
    
    Args:
        filename: Name of file
        file_path: Path to file
        
    Returns:
        tuple: (is_valid, error_msg, dataframe)
    """
    try:
        validate_file_extension(filename)
        validate_file_size(file_path)
        df, error = validate_csv_content(file_path)
        
        if error:
            return False, error, None
        
        return True, None, df
    
    except ValidationError as e:
        return False, str(e), None
    except Exception as e:
        return False, f"Unexpected error: {str(e)}", None
