import boto3
from datetime import datetime, timezone
from botocore.exceptions import ClientError


def send_email_via_ses(sender, recipients, subject, message):
    ses = boto3.client('ses', region_name='us-east-1')
    try:
        response = ses.send_email(
            Source=sender,
            Destination={'ToAddresses': recipients},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Text': {'Data': message}}
            }
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'MessageRejected':
            print(f"Email sending failed due to unverified email address. Error: {e}")
        else:
            print(f"An unexpected error occurred: {e}")


def format_owner_email(instance_id, instance_name, instance_warning):
    header = [
        f"This is an automated runtime warning for EC2 instance {instance_name} ({instance_id}). Please review the details below."]
    return "\n".join(header + instance_warning)


def format_admin_email(instance_warnings):
    header = [f"This is an automated runtime warning for EC2 instances. Please review the details below."]
    body = [inst_txt for inst_txt in instance_warnings]
    return "\n\n".join(header + body)


def lambda_handler(event, context):
    ec2 = boto3.client('ec2')
    admin_emails = []  # admin emails recieve alerts for all instances
    sender = ''  # email from which to send alerts
    subject = 'EC2 Instance Runtime Alert'

    threshold_hrs = 48  # send alerts for all instance running > threshold time

    # Get all EC2 instances that are running
    instances = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
    print(f"instance_name  |  instance_id  |  runtime (hrs)  |  launch_time")

    all_instance_warnings = []
    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']

            # Check if the instance has the AlwaysOn tag set to True and skip notification
            always_on = any(tag['Value'] == 'True' for tag in instance.get('Tags', []) if tag['Key'] == 'AlwaysOn')
            if always_on:
                continue

            instance_name = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), 'Unknown')
            owner_email = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'].lower() == 'email'),
                               None)

            # Calculate runtime
            launch_time = instance['LaunchTime']
            launch_time_str = launch_time.strftime('%Y-%m-%d %H:%M:%S %Z')
            current_time = datetime.now(timezone.utc)
            runtime = current_time - launch_time
            runtime_hrs = runtime.total_seconds() / 3600

            print(f"{instance_name}  |  ({instance_id})  |  {"%.2f" % runtime_hrs}  |  {launch_time_str}")

            if runtime_hrs > threshold_hrs:
                instance_warning = [
                    "Instance Details:",
                    f"- Instance Name: {instance_name}",
                    f"- Instance ID: {instance_id}",
                    f"- Current Runtime: {'%.2f' % runtime_hrs} hours",
                    f"- Region: {instance['Placement']['AvailabilityZone']}",
                    f"- Instance Type: {instance['InstanceType']}",
                    f"- Launch Time: {launch_time_str}",
                    f"- User Email: {owner_email if owner_email else 'N/A'}"]
                all_instance_warnings.append("\n".join(instance_warning))

                if owner_email:
                    owner_message = format_owner_email(instance_id, instance_name, instance_warning)
                    send_email_via_ses(sender, [owner_email], subject, owner_message)

    if all_instance_warnings:
        admin_message = format_admin_email(all_instance_warnings)
        for recipient in admin_emails:
            send_email_via_ses(sender, [recipient], subject, admin_message)

    return {
        'statusCode': 200,
        'body': 'Execution completed'
    }
