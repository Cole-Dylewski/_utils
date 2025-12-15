# Usage Examples

## AWS S3 Operations

```python
from _utils.aws import s3

# Initialize S3 handler
handler = s3.S3Handler()

# Upload DataFrame to S3
handler.send_to_s3(
    data=df,
    bucket='my-bucket',
    s3_file_name='data.csv'
)

# Download from S3 to DataFrame
df = handler.s3_to_df(
    bucket='my-bucket',
    object_key='data.csv'
)
```

## Alpaca Trading

```python
from _utils.alpaca import TraderClient

# Initialize client
client = TraderClient(
    api_key='your-api-key',
    api_secret='your-api-secret'
)

# Get account information
account = client.get_account()

# Submit order
order = client.submit_order(
    symbol='AAPL',
    qty=10,
    side='buy',
    order_type='market',
    time_in_force='gtc'
)

# Get positions
positions = client.get_positions()
```

## Database Operations

```python
from _utils.utils import sql

# Execute SQL query
result = sql.run_sql(
    query="SELECT * FROM users WHERE active = true",
    queryType='query',
    dbname='production',
    rds='postgres'
)

# Generate INSERT statement from DataFrame
insert_stmt = sql.df_to_insert_stmt(df, 'schema.table')
```

## Tableau Integration

```python
from _utils.utils import tableau

# Create Tableau client
client = tableau.tableau_client(
    username='user',
    password='pass',
    server_url='https://tableau.example.com'
)

# Generate report
with client:
    client.login()
    files = client.generate_report(
        view_ids=['view-123'],
        filename='report.pdf',
        merge=True
    )
```

## Infrastructure Automation

```python
from _utils.server_management import TerraformHandler, AnsibleHandler

# Terraform operations
tf = TerraformHandler(project_dir="./terraform")
tf.init()
tf.plan()
tf.apply()

# Ansible playbook execution
ansible = AnsibleHandler(
    ansible_dir="./ansible",
    inventory="hosts.yml"
)
ansible.run_playbook(
    "setup.yml",
    extra_vars={"app_version": "1.0.0"}
)
```
