"""
Examples of creating custom filters
"""

from postgres_backup_plugin import PostgresBackupEngine, DatabaseConfig
from postgres_backup_plugin.filters import FilterQuery, CompositeFilter, DateRangeFilter, StatusFilter


class AgeRangeFilter(FilterQuery):
    """Custom filter: Filter users by age range"""

    def __init__(self, min_age, max_age):
        self.min_age = min_age
        self.max_age = max_age

    def build(self, table_name, **params):
        return f"""
            SELECT * FROM {table_name}
            WHERE age BETWEEN {self.min_age} AND {self.max_age}
        """

    def __str__(self):
        return f"AgeRangeFilter({self.min_age}-{self.max_age})"


class GeoLocationFilter(FilterQuery):
    """Custom filter: Filter by geographic location"""

    def __init__(self, country=None, state=None, city=None):
        self.country = country
        self.state = state
        self.city = city

    def build(self, table_name, **params):
        conditions = []

        if self.country:
            conditions.append(f"country = '{self.country}'")
        if self.state:
            conditions.append(f"state = '{self.state}'")
        if self.city:
            conditions.append(f"city = '{self.city}'")

        if not conditions:
            return f"SELECT * FROM {table_name}"

        where_clause = " AND ".join(conditions)
        return f"SELECT * FROM {table_name} WHERE {where_clause}"


class RecentActivityFilter(FilterQuery):
    """Custom filter: Filter by recent activity (last N days)"""

    def __init__(self, activity_column='last_login', days=30):
        self.activity_column = activity_column
        self.days = days

    def build(self, table_name, **params):
        return f"""
            SELECT * FROM {table_name}
            WHERE {self.activity_column} >= NOW() - INTERVAL '{self.days} days'
        """


def example_custom_filters():
    """Use custom filters"""
    print("=== Custom Filters Example ===\n")

    db_config = DatabaseConfig(
        host='localhost',
        user='postgres',
        password='your_password',
        database='mydb'
    )

    engine = PostgresBackupEngine(db_config)

    # Use custom filters
    filters = {
        'users': AgeRangeFilter(18, 65),
        'customers': GeoLocationFilter(country='US', state='CA'),
        'accounts': RecentActivityFilter(days=90)
    }

    result = engine.backup(
        output_path='/tmp/custom_filtered_backup.sql',
        filters=filters
    )

    if result.success:
        print(f"✅ Custom filtered backup successful!")
        for table, stats in result.stats['tables'].items():
            print(f"   - {table}: {stats['rows']} rows")


def example_composite_filters():
    """Combine multiple filters"""
    print("\n=== Composite Filters Example ===\n")

    db_config = DatabaseConfig(
        host='localhost',
        user='postgres',
        password='your_password',
        database='mydb'
    )

    engine = PostgresBackupEngine(db_config)

    # Combine filters with AND
    date_filter = DateRangeFilter('created_at', '2024-01-01', '2024-12-31')
    status_filter = StatusFilter('status', allowed_statuses=['active', 'pending'])

    composite = CompositeFilter(date_filter, status_filter, operator='AND')

    filters = {
        'orders': composite,
        'shipments': DateRangeFilter('shipped_date', '2024-01-01', '2024-12-31')
    }

    result = engine.backup(
        output_path='/tmp/composite_filtered_backup.sql',
        filters=filters
    )

    if result.success:
        print(f"✅ Composite filtered backup successful!")
        print(f"   Total rows: {result.total_rows:,}")


def example_complex_business_logic():
    """Complex business logic filter"""
    print("\n=== Complex Business Logic Example ===\n")

    class HighValueCustomerFilter(FilterQuery):
        """Filter high-value customers with specific criteria"""

        def __init__(self, min_lifetime_value, min_orders):
            self.min_lifetime_value = min_lifetime_value
            self.min_orders = min_orders

        def build(self, table_name, **params):
            return f"""
                SELECT c.*
                FROM {table_name} c
                INNER JOIN (
                    SELECT customer_id,
                           COUNT(*) as order_count,
                           SUM(total_amount) as lifetime_value
                    FROM orders
                    GROUP BY customer_id
                ) o ON c.id = o.customer_id
                WHERE o.lifetime_value >= {self.min_lifetime_value}
                  AND o.order_count >= {self.min_orders}
                  AND c.status = 'active'
            """

    db_config = DatabaseConfig(
        host='localhost',
        user='postgres',
        password='your_password',
        database='mydb'
    )

    engine = PostgresBackupEngine(db_config)

    filters = {
        'customers': HighValueCustomerFilter(min_lifetime_value=10000, min_orders=5)
    }

    result = engine.backup(
        output_path='/tmp/high_value_customers_backup.sql',
        filters=filters
    )

    if result.success:
        print(f"✅ High-value customers backup successful!")
        print(f"   Customers exported: {result.stats['tables']['customers']['rows']}")


if __name__ == '__main__':
    example_custom_filters()
    example_composite_filters()
    example_complex_business_logic()
