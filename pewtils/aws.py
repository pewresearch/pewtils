import boto3
import datetime


def create_rds_snapshot(instance_name=None, snapshot_name=None, tags=None):

    """
    creates snapshot of rds instance
    
    """

    db = boto3.client("rds")
    return db.create_db_snapshot(
        DBInstanceIdentifier=instance_name,
        DBSnapshotIdentifier=snapshot_name if snapshot_name \
            else '{}-{}'.format(instance_name, datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')),
        Tags=tags if tags else []
    )
