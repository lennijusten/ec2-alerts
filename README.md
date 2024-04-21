# EC2 Runtime Alerts for AWS
This AWS Lambda function sends runtime alerts for EC2 instances that have been running longer than a specified threshold. The Lambda function is triggered by the Amazon EventBridge Scheduler and sends email notifications via the Simple Notification Service (SNS).

## Configuration
To set up the function, you must specify a `sender` email address from which the alerts will be sent. Additionally, you can set `admin_emails` to receive runtime alerts for all instances associated with the AWS account. If you want to exclude instances that are always on from runtime notifications, you can add a `AlwaysOn` tag with the value set to `True`.  

## User Subscription
When launching a new EC2 instance, users can subscribe to runtime alerts by adding an `Email` tag to the instance. User emails must be subscribed to the SNS topic, which can be done by either subscribing an entire domain or subscribing individual email addresses. Note that subscribing individual emails requires a one-time verification process.

## Example Output
Here is an example of the output from the admin view:
```markdown
This is an automated runtime warning for EC2 instances. Please review the details below.

Instance Details:

Instance ID: i-xxxxxxxxxxxx
Instance Name: instanceA
Current Runtime: 50.50 hours
Region: us-east-1a
Instance Type: c6a.8xlarge
Launch Time: 2024-01-31 22:29:40 UTC

Instance Details:

Instance ID: i-yyyyyyyyyyyy
Instance Name: instanceB
Current Runtime: 101.72 hours
Region: us-east-1f
Instance Type: g4dn.xlarge
Launch Time: 2024-01-29 19:16:43 UTC
```