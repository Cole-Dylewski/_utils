# app/clients/snowpark_client.py
from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
import os
from typing import Any, Optional

try:
    from snowflake.snowpark import DataFrame, Session
    from snowflake.snowpark import functions as F
    from snowflake.snowpark import types as spt
except ImportError:
    # snowflake-snowpark-python is an optional dependency
    # Define minimal stubs for type checking when not installed
    DataFrame = Any  # type: ignore
    Session = Any  # type: ignore
    F = Any  # type: ignore
    spt = Any  # type: ignore

ConfigDict = dict[str, Any]
SqlParams = Optional[Sequence[Any] | dict[str, Any]]


@dataclass
class SnowparkClient:
    """
    Thin convenience wrapper around Snowflake Snowpark Session.

    Create with `SnowparkClient.from_env()` or pass a config dict matching
    `Session.builder.configs(...)` keys (e.g., ACCOUNT, USER, PASSWORD, ROLE, WAREHOUSE, DATABASE, SCHEMA).

    Example:
        client = SnowparkClient.from_env()
        with client as sp:
            df = sp.table("MY_DB.MY_SCHEMA.MY_TABLE").limit(5)
            rows = df.collect()
            print(rows)
    """

    configs: ConfigDict
    _session: Session | None = field(default=None, init=False, repr=False)

    # ---------- Construction ----------
    @staticmethod
    def from_env(prefix: str = "SNOWFLAKE_") -> SnowparkClient:
        """
        Build a client from environment variables. Expected keys with given prefix:
          ACCOUNT, USER, PASSWORD (or AUTHENTICATOR/OAUTH), ROLE, WAREHOUSE, DATABASE, SCHEMA
        Any additional Snowflake connector keys can be supplied and will be passed through.

        Example env:
          SNOWFLAKE_ACCOUNT=xy12345.us-east-1
          SNOWFLAKE_USER=me
          SNOWFLAKE_PASSWORD=...
          SNOWFLAKE_ROLE=SYSADMIN
          SNOWFLAKE_WAREHOUSE=COMPUTE_WH
          SNOWFLAKE_DATABASE=MY_DB
          SNOWFLAKE_SCHEMA=PUBLIC
        """
        # Collect all SNOWFLAKE_* envs (upper-cased keys without prefix become builder keys)
        cfg: ConfigDict = {}
        plen = len(prefix)
        for k, v in os.environ.items():
            if k.startswith(prefix):
                cfg[k[plen:]] = v
        if not cfg:
            raise RuntimeError(
                f"No environment variables found with prefix {prefix!r}. "
                "Set SNOWFLAKE_* values or pass explicit configs."
            )
        return SnowparkClient(cfg)

    # ---------- Context manager ----------
    def __enter__(self) -> SnowparkClient:
        self._ensure_session()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    # ---------- Session lifecycle ----------
    def _ensure_session(self) -> Session:
        if self._session is None:
            self._session = Session.builder.configs(self.configs).create()
        return self._session

    @property
    def session(self) -> Session:
        return self._ensure_session()

    def close(self) -> None:
        if self._session is not None:
            try:
                self._session.close()
            finally:
                self._session = None

    # ---------- Quick helpers ----------
    def run(
        self,
        sql: str,
        params: SqlParams = None,
        *,
        collect: bool = True,
        to_pandas: bool = False,
    ) -> list[Any] | DataFrame | pandas.DataFrame:
        """
        Execute arbitrary SQL.

        Args:
            sql: SQL string (use named or positional binds).
            params: Optional parameters for the SQL.
            collect: If True, executes and collects rows. If False, returns a Snowpark DataFrame.
            to_pandas: If True and collect=True, converts result to pandas DataFrame.

        Returns:
            List[Row] if collect, DataFrame if not, or pandas.DataFrame if to_pandas.
        """
        df = self.session.sql(sql, params=params)
        if not collect:
            return df
        if to_pandas:
            return df.to_pandas()
        return df.collect()

    def table(self, name: str) -> DataFrame:
        """Return a Snowpark DataFrame for a fully qualified table name."""
        return self.session.table(name)

    def create_dataframe(
        self,
        data: Iterable[tuple[Any, ...]] | Iterable[dict[str, Any]],
        schema: spt.StructType | list[str] | None = None,
    ) -> DataFrame:
        """
        Create a Snowpark DataFrame from local data.

        `schema` can be a StructType or list of column names.
        """
        return self.session.create_dataframe(data, schema=schema)

    # ---------- Writes ----------
    def write_dataframe(
        self,
        df: DataFrame,
        table_name: str,
        mode: str = "append",
        *,
        overwrite: bool | None = None,
        column_order: str = "name",
        create_table_column_types: dict[str, spt.DataType] | None = None,
    ) -> None:
        """
        Save a Snowpark DataFrame to a table.

        Args:
            mode: "append" or "overwrite". (If both `mode` and `overwrite` provided, `overwrite` wins.)
            overwrite: True to replace table; False to append.
        """
        writer = df.write
        if overwrite is True or mode == "overwrite":
            writer = writer.mode("overwrite")
        else:
            writer = writer.mode("append")
        writer.save_as_table(
            table_name,
            column_order=column_order,
            create_table_column_types=create_table_column_types,
        )

    def write_pandas(
        self,
        pdf: pandas.DataFrame,
        table_name: str,
        *,
        overwrite: bool = False,
        auto_create_table: bool = True,
        quote_identifiers: bool = True,
    ) -> None:
        """
        Write a pandas DataFrame to a Snowflake table.

        Uses Session.write_pandas if available; otherwise falls back to connector utility.
        """
        # Prefer Snowpark Session API if present
        if hasattr(self.session, "write_pandas"):
            self.session.write_pandas(
                pdf,
                table_name=table_name,
                auto_create_table=auto_create_table,
                overwrite=overwrite,
                quote_identifiers=quote_identifiers,
            )
            return

        # Fallback to connector helper
        from snowflake.connector.pandas_tools import write_pandas  # type: ignore

        conn = self.session._conn._conn  # internal, but commonly used for fallback
        write_pandas(
            conn,
            pdf,
            table_name,
            quote_identifiers=quote_identifiers,
            auto_create_table=auto_create_table,
            overwrite=overwrite,
        )

    # ---------- Procedures & UDFs ----------
    def call_procedure(self, name: str, *args: Any) -> Any:
        """Call a stored procedure by name (can be fully qualified)."""
        return self.session.call(name, *args)

    def register_udf(
        self,
        func: Callable[..., Any],
        return_type: spt.DataType,
        input_types: Sequence[spt.DataType],
        *,
        name: str | None = None,
        replace: bool = True,
        is_permanent: bool = False,
        stage_location: str | None = None,
        packages: Sequence[str] | None = None,
    ) -> F.UserDefinedFunction:
        """
        Register a Python UDF.

        If `is_permanent=True`, provide `stage_location='@my_stage'` (and ensure perms).
        """
        return self.session.udf.register(
            func=func,
            return_type=return_type,
            input_types=list(input_types),
            name=name,
            replace=replace,
            is_permanent=is_permanent,
            stage_location=stage_location,
            packages=list(packages) if packages else None,
        )

    def register_stored_procedure(
        self,
        func: Callable[..., Any],
        return_type: spt.DataType,
        input_types: Sequence[spt.DataType],
        *,
        name: str | None = None,
        replace: bool = True,
        is_permanent: bool = True,
        stage_location: str | None = None,
        packages: Sequence[str] | None = None,
        execute_as: str = "owner",
    ) -> F.StoredProcedureRegistration:
        """
        Register a Python stored procedure.

        Stored procedures are typically permanent; set `stage_location` to an internal stage like '@proc_stage'.
        """
        return self.session.sproc.register(
            func=func,
            return_type=return_type,
            input_types=list(input_types),
            name=name,
            replace=replace,
            is_permanent=is_permanent,
            stage_location=stage_location,
            packages=list(packages) if packages else None,
            execute_as=execute_as,
        )

    # ---------- Quality-of-life ----------
    def to_pandas(self, df: DataFrame, *, timezone: str | None = None) -> pandas.DataFrame:
        """
        Convert a Snowpark DataFrame to pandas. Optionally set timezone for timestamp conversions.
        """
        if timezone:
            return df.to_pandas(timezone=timezone)
        return df.to_pandas()

    def current(self) -> dict[str, str]:
        """Return current context (database, schema, role, warehouse)."""
        rows = self.session.sql(
            "select current_database(), current_schema(), current_role(), current_warehouse()"
        ).collect()
        db, schema, role, wh = rows[0][0], rows[0][1], rows[0][2], rows[0][3]
        return {"database": db, "schema": schema, "role": role, "warehouse": wh}
