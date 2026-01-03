"""
S3 storage utilities for persisting preprocessed tables.

Handles uploading and downloading preprocessed DataFrames to/from S3 as CSV files.
Uses Streamlit secrets for AWS credentials configuration.
"""

import pandas as pd
import boto3
import streamlit as st
from botocore.exceptions import ClientError, NoCredentialsError
from io import BytesIO
from typing import Optional, Tuple


def get_s3_client():
    """
    Get S3 client using Streamlit secrets.
    
    Returns:
        boto3 S3 client configured with credentials from secrets
        
    Raises:
        ValueError: If AWS credentials are missing from Streamlit secrets
    """
    try:
        return boto3.client(
            's3',
            aws_access_key_id=st.secrets["aws"]["access_key_id"],
            aws_secret_access_key=st.secrets["aws"]["secret_access_key"]
        )
    except KeyError as e:
        raise ValueError(f"Missing AWS credentials in Streamlit secrets: {e}")
    except Exception as e:
        raise ValueError(f"Error configuring S3 client: {str(e)}")


def get_s3_config() -> Tuple[str, str]:
    """
    Get bucket name and S3 key from secrets.
    
    Returns:
        Tuple of (bucket_name, s3_key)
        
    Raises:
        ValueError: If S3 configuration is missing from Streamlit secrets
    """
    try:
        return st.secrets["aws"]["bucket_name"], st.secrets["aws"]["s3_key"]
    except KeyError as e:
        raise ValueError(f"Missing S3 configuration in Streamlit secrets: {e}")


def check_s3_table_exists() -> bool:
    """
    Check if preprocessed table exists in S3.
    
    Returns:
        True if table exists, False otherwise
    """
    try:
        s3_client = get_s3_client()
        bucket_name, s3_key = get_s3_config()
        s3_client.head_object(Bucket=bucket_name, Key=s3_key)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            return False
        # Re-raise other client errors (permissions, etc.)
        st.error(f"S3 error checking for table: {str(e)}")
        return False
    except ValueError:
        # Missing credentials/config - return False gracefully
        return False
    except Exception as e:
        st.warning(f"Unexpected error checking S3: {str(e)}")
        return False


def load_table_from_s3() -> Optional[pd.DataFrame]:
    """
    Load preprocessed table from S3 as DataFrame.
    
    Returns:
        DataFrame loaded from S3, or None if error occurs
    """
    try:
        s3_client = get_s3_client()
        bucket_name, s3_key = get_s3_config()
        
        response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
        csv_bytes = response['Body'].read()
        
        df = pd.read_csv(BytesIO(csv_bytes))
        return df
    except ValueError as e:
        # Missing credentials/config
        st.error(f"Configuration error: {str(e)}")
        return None
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchKey':
            st.error(f"Table not found in S3: {s3_key}")
        else:
            st.error(f"S3 error loading table: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error loading table from S3: {str(e)}")
        return None


def save_table_to_s3(df: pd.DataFrame) -> bool:
    """
    Save DataFrame to S3 as CSV, replacing existing if present.
    
    Args:
        df: DataFrame to save
        
    Returns:
        True if successful, False otherwise
    """
    try:
        s3_client = get_s3_client()
        bucket_name, s3_key = get_s3_config()
        
        # Convert DataFrame to CSV bytes
        csv_buffer = BytesIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        
        # Upload to S3 (this replaces existing file if it exists)
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=csv_buffer.getvalue(),
            ContentType='text/csv'
        )
        return True
    except ValueError as e:
        # Missing credentials/config
        st.error(f"Configuration error: {str(e)}")
        return False
    except ClientError as e:
        st.error(f"S3 error saving table: {str(e)}")
        return False
    except Exception as e:
        st.error(f"Error saving table to S3: {str(e)}")
        return False

