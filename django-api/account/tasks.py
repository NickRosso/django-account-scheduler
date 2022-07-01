
from celery import shared_task
from datetime import datetime
from account.models import Account

@shared_task
def get_account_ids_to_run(account_ids_list):
    """This function uses a list of account IDs to do some basic arithmetic with Modulus, and the current time to
    group the IDs into sync groups. Modulus is helpful here because we can reliably assign a sync group evenly based off of only the account ID.
    As the account ID grows assuming no account ID is removed it will evenly distribute the account ID's into the number of groups (interval).
    To configure this to run at different time frequencies simply update time_frequency from minute, to hour, or to day and then schedule this to run hourly, or daily.
    Example for time_frequency = 'minute'.
        For example if the ID is 15: we do 15 % 15 = 0 so the account will be returned at 0,15,30,45 minutes in the hour.
        For example if the ID is 16: we do 16 % 15 = 1 so the account wil be returned at 1,16,31,46 minutes in the hour.
        For example if the ID is 1000: we do 1000 % 15 = 10 so the account wil be returned at 10,25,40,55 minutes in the hour.
    Example for time_frequency = 'hourly'
        For example if the ID is 15: we do 15 % 24 = 24 so the account will be returned at 24th hour per day.
    Example for time_frequency = 'daily'
        For example if the ID is 15: we do 15 % 31 = 15 so the account will be returned on the 15th day per month. Note since months are variable, there may be less synced
        on days at the end of longer months.

    Returns account_ids_list a list of Account ID's
    """
    account_ids_to_return = []
    time_frequency = 'minute'

    if time_frequency == 'minute':
        interval = 15 # interval is used calculate the current time's sync group and the account id's sync group
        sync_group = datetime.now().minute % interval
    elif time_frequency == 'hour':
        interval = 24
        sync_group = datetime.now().hour % interval
    elif time_frequency == 'day':
        interval = 31
        sync_group = datetime.now().day % interval

    for account_id in account_ids_list:
        account_sync_group = account_id % interval # calculates the accounts sync group

        if account_sync_group == sync_group: #determines if the accounts sync group is equal to the current time's sync group
            account_ids_to_return.append(account_id)
            synchronize_account.apply_async(args=[account_id])

    return account_ids_to_return 



@shared_task
def synchronize_account(account_id):
    account_object = Account.objects.get(id=account_id)
    account_object.save()
    print(account_object.last_synchronized)