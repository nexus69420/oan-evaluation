"""LogFire API client for fetching and processing log data."""
import os
import asyncio
import datetime as dt
from logfire.query_client import AsyncLogfireQueryClient
from typing import Optional, List, Dict, Any
from tqdm import tqdm


# Default columns to fetch if none specified
DEFAULT_COLUMNS = ["span_id","created_at","attributes"]


class LogFireClient:
    """Async client for interacting with LogFire API using the official SDK."""
    
    def __init__(
        self,
        read_token: Optional[str] = None,
    ):
        """Initialize LogFire API client.

        Args:
            read_token: API read token (defaults to env LOGFIRE_READ_TOKEN)
        """
        self.read_token = read_token or os.getenv('LOGFIRE_READ_TOKEN')
        if not self.read_token:
            raise ValueError(
                "API token must be provided via read_token parameter or "
                "LOGFIRE_READ_TOKEN environment variable"
            )

    async def fetch_logs(
        self,
        columns: Optional[List[str]] = None,
        start_at: dt.datetime = dt.datetime(2025, 5, 24, tzinfo=dt.timezone.utc),
        end_at: dt.datetime = dt.datetime.now(dt.timezone.utc),
        minutes_window: int = 1440,
        agent_name: Optional[str] = None,
        rate_limit_pause: float = 0.3,
        include_exceptions: bool = False,
    ) -> Dict[str, Any]:
        """Fetch logs from LogFire API with pagination.

        Args:
            columns: List of column names to fetch (defaults to DEFAULT_COLUMNS)
            start_at: Start timestamp for log fetch (defaults to 5 months ago)
            end_at: End timestamp for log fetch (defaults to current UTC time)
            minutes_window: Time window size for each API request in minutes (defaults to 1440 minutes = 24 hours)
            agent_name: Agent name to filter logs by
            rate_limit_pause: Pause duration between requests in seconds
            include_exceptions: Whether to include exception records (default False)

        Returns:
            Polars DataFrame containing all fetched logs
        """
        # Construct base SQL query
        cols = columns if columns is not None else DEFAULT_COLUMNS
        base_sql = f"SELECT {', '.join(cols)} FROM records"
        
        # Add exception filter if needed
        if not include_exceptions:
            base_sql = f"{base_sql} WHERE is_exception = FALSE"

        results = []
        cursor = start_at
        
        # Calculate total number of chunks for progress bar
        total_chunks = int((end_at - start_at).total_seconds() / (minutes_window * 60)) + 1

        async with AsyncLogfireQueryClient(read_token=self.read_token) as client:
            with tqdm(total=total_chunks, desc="Fetching log chunks") as pbar:
                while cursor < end_at:
                    slice_end = min(cursor + dt.timedelta(seconds=minutes_window * 60), end_at)
                    
                    try:
                        chunk_data = await self._fetch_slice(client, base_sql, cursor, slice_end, agent_name)
                        if chunk_data and chunk_data.get("columns"):
                            results.append(chunk_data)
                    except Exception as e:
                        print(f"Error fetching slice {cursor} to {slice_end}: {e}")
                        continue  # Skip failed chunks and continue with next

                    cursor = slice_end
                    pbar.update(1)
                    await asyncio.sleep(rate_limit_pause)

        # Combine all chunks into a list of records
        if not results:
            return []
            
        # Convert column-oriented data to row-oriented
        records = []
        
        # First, build a map of column names to their values
        col_values = {}
        for chunk in results:
            for col in chunk["columns"]:
                col_name = col["name"]
                if col_name not in col_values:
                    col_values[col_name] = []
                col_values[col_name].extend(col["values"])
        
        # Now create a record for each row
        num_rows = len(next(iter(col_values.values())))  # Length of any column
        for i in range(num_rows):
            record = {}
            for col_name, values in col_values.items():
                record[col_name] = values[i]
            
            records.append(record)
        
        print(
            f"Fetched {len(records)} records spanning {start_at.date()} → {end_at.date()}"
        )
        return records

    async def _fetch_slice(
        self,
        client: AsyncLogfireQueryClient,
        sql: str,
        min_ts: dt.datetime,
        max_ts: dt.datetime,
        agent_name: Optional[str] = None,
        limit: int = 10_000,
    ) -> Dict[str, Any]:
        """Fetch a single time slice of logs using the LogFire SDK.

        Args:
            client: Async LogFire query client
            sql: SQL query to execute
            min_ts: Start timestamp for this slice
            max_ts: End timestamp for this slice
            agent_name: Agent name to filter logs by
            limit: Maximum number of rows to fetch

        Returns:
            Polars DataFrame containing logs for the time slice
        """
        # Modify query to include time range and limit
        filters = []
        if agent_name:
            filters.append(f"attributes->>'agent_name' = '{agent_name}'")
        if min_ts:
            filters.append(f"start_timestamp >= '{min_ts.isoformat()}'")
        if max_ts:
            filters.append(f"start_timestamp < '{max_ts.isoformat()}'")
        
        # Build the filter clause with proper WHERE/AND syntax
        base_sql = sql.rstrip(';').strip()
        if filters:
            filter_clause = " AND ".join(filters)
            # Check if base query already has WHERE clause
            if "WHERE" in base_sql.upper():
                query_with_filters = f"{base_sql} AND {filter_clause} LIMIT {limit}"
            else:
                query_with_filters = f"{base_sql} WHERE {filter_clause} LIMIT {limit}"
        else:
            query_with_filters = f"{base_sql} LIMIT {limit}"
        
        # Use query_json for JSON output
        return await client.query_json(sql=query_with_filters)

    async def query_json(self, sql: str) -> dict:
        """Execute a query and return results as JSON in column-oriented format.

        Args:
            sql: SQL query to execute

        Returns:
            Dictionary with query results in column-oriented format
        """
        async with AsyncLogfireQueryClient(read_token=self.read_token) as client:
            return await client.query_json(sql=sql)

    async def query_json_rows(self, sql: str) -> dict:
        """Execute a query and return results as JSON in row-oriented format.

        Args:
            sql: SQL query to execute

        Returns:
            Dictionary with query results in row-oriented format
        """
        async with AsyncLogfireQueryClient(read_token=self.read_token) as client:
            return await client.query_json_rows(sql=sql)


    async def get_info(self) -> dict:
        """Get information about the read token.

        Returns:
            Dictionary with read token information
        """
        async with AsyncLogfireQueryClient(read_token=self.read_token) as client:
            return await client.info()
