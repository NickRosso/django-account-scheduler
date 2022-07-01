## Instructions to Run 

```
docker-compose build
docker-compose up
```

## Narrative
When I first approached this problem I thought I would need to have some mechanism to store what time the the account was last synced and use that to calculate the groupings based of that. The problem here is i would need another function just to set the last synced date properly so it could be used to filter on records that havent been synced for 15 minutes.
I opted to not use this approach because this approach I would've needed to add a few fields to the Account Modal. This approach also would be BAD for if the service went down and when you restarted it every account would be old and be triggered to be resynced. This wouldnt work well..

My second approach was to create a dictionary of lists.
the idea was that the key was the minute of the hour up till the 15th minute. The function would then loop over all the account ID's and evenly distribute them to the key in the dictionary.
But again I would need a method to determine what key in the dictionary to return as the IDs that needed to be ranbased on the current time. This would also break the idea that the accounts would have to be synced every X minutes. Some accounts would be synced way longer than that and it wouldnt be reliable.

After tinkering with those I went on a walk with my Dog and thought there had to be a simpler way just using the AccountID.
I had an idea to use the modulus operator to group the account ID's. In my past I've used the modulus operator to determine if something is even or odd, but i thought it could work great for many more groupings. Since modulus returns the remainder of the divisor it makes it great for calculating multiple numbers. I am proud of my solution since it is pretty elegant, and it is fast. Please run this locally and see the celery workers in action yourself :)

## Here is the Code Snippet that does the magic
```django-api/account/tasks.py

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
```

## Visit http:/localhost:8000/admin to view accounts and see when they were last synced

Example Celery work output
```
[2022-04-02 13:29:00,337: INFO/ForkPoolWorker-2] Task account.tasks.get_account_ids_to_run[fb21f7b0-3c8a-4778-bc43-06e058373394] succeeded in 0.32837020000079065s: [14, 
29, 44, 59, 74, 89, 104, 119, 134, 149, 164, 179, 194, 209, 224, 239, 254, 269, 284, 299, 314, 329, 344, 359, 374, 389, 404, 419, 434, 449, 464, 479, 494]

[2022-04-02 13:30:00,321: INFO/ForkPoolWorker-2] Task account.tasks.get_account_ids_to_run[4852f235-cb9f-4aa5-888c-a2cbc9a5c4d1] succeeded in 0.31141650000063237s: [15, 
30, 45, 60, 75, 90, 105, 120, 135, 150, 165, 180, 195, 210, 225, 240, 255, 270, 285, 300, 315, 330, 345, 360, 375, 390, 405, 420, 435, 450, 465, 480, 495]

[2022-04-02 13:31:00,344: INFO/ForkPoolWorker-2] Task account.tasks.get_account_ids_to_run[56cd6259-5c99-4fd6-b92f-1c1ac804c06e] succeeded in 0.33437119999871356s: [1,
 16, 31, 46, 61, 76, 91, 106, 121, 136, 151, 166, 181, 196, 211, 226, 241, 256, 271, 286, 301, 316, 331, 346, 361, 376, 391, 406, 421, 436, 451, 466, 481, 496]

[2022-04-02 13:32:00,351: INFO/ForkPoolWorker-2] Task account.tasks.get_account_ids_to_run[62e354c8-8a7d-47c1-b219-6f9b50bf7736] succeeded in 0.34288369999921997s: [2,
 17, 32, 47, 62, 77, 92, 107, 122, 137, 152, 167, 182, 197, 212, 227, 242, 257, 272, 287, 302, 317, 332, 347, 362, 377, 392, 407, 422, 437, 452, 467, 482, 497]

[2022-04-02 13:33:00,300: INFO/ForkPoolWorker-2] Task account.tasks.get_account_ids_to_run[8c9da25b-9ebd-4736-b728-0f4066ef34c5] succeeded in 0.2940263000000414s: [3, 
 18, 33, 48, 63, 78, 93, 108, 123, 138, 153, 168, 183, 198, 213, 228, 243, 258, 273, 288, 303, 318, 333, 348, 363, 378, 393, 408, 423, 438, 453, 468, 483, 498]

[2022-04-02 13:34:00,322: INFO/ForkPoolWorker-2] Task account.tasks.get_account_ids_to_run[d25160ec-d8ba-4397-a2f1-a0e5b6957de9] succeeded in 0.3158784999995987s: [4,
 19, 34, 49, 64, 79, 94, 109, 124, 139, 154, 169, 184, 199, 214, 229, 244, 259, 274, 289, 304, 319, 334, 349, 364, 379, 394, 409, 424, 439, 454, 469, 484, 499]

[2022-04-02 13:35:00,359: INFO/ForkPoolWorker-2] Task account.tasks.get_account_ids_to_run[0a61e0e0-7773-45c5-8af7-df3f36ce9618] succeeded in 0.3523451000000932s: [5,
 20, 35, 50, 65, 80, 95, 110, 125, 140, 155, 170, 185, 200, 215, 230, 245, 260, 275, 290, 305, 320, 335, 350, 365, 380, 395, 410, 425, 440, 455, 470, 485]

[2022-04-02 13:36:00,364: INFO/ForkPoolWorker-2] Task account.tasks.get_account_ids_to_run[c23ce3bf-f1d8-4d97-93a5-a4e83cb32561] succeeded in 0.35941749999983585s: [6,
 21, 36, 51, 66, 81, 96, 111, 126, 141, 156, 171, 186, 201, 216, 231, 246, 261, 276, 291, 306, 321, 336, 351, 366, 381, 396, 411, 426, 441, 456, 471, 486]

[2022-04-02 13:46:00,325: INFO/ForkPoolWorker-2] Task account.tasks.get_account_ids_to_run[06bf59c9-35db-4ef9-a1af-7d69d820db57] succeeded in 0.3175859999992099s: [1,
 16, 31, 46, 61, 76, 91, 106, 121, 136, 151, 166, 181, 196, 211, 226, 241, 256, 271, 286, 301, 316, 331, 346, 361, 376, 391, 406, 421, 436, 451, 466, 481, 496]
```