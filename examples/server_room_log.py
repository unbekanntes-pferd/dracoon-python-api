"""
Export Room Log DRACOON Server
24.02.2021 Quirin Wierer
"""

from dracoon import DRACOON
import asyncio
import csv
 
async def main():
    baseURL = 'https://dracoon.server'
    client_id = 'XXXXXXXXXXX'
    client_secret = 'XXXXXXXXXX'
    ROOM_ID = 19
    START_DATE = '2015-12-31T23:59:00'
    END_DATE = '2022-02-24T23:59:00'
    fileName = 'Report of Dataroom '+str(ROOM_ID)+' '+START_DATE+' - '+END_DATE+'.csv'


    #authenticate
    dracoon = DRACOON(base_url=baseURL, client_id=client_id, client_secret=client_secret)
    print(dracoon.get_code_url())

    auth_code = input('Enter auth code:')
    await dracoon.connect(auth_code=auth_code)

    
    # retrieve roomlogs
    roomevents = await dracoon.nodes.get_room_events(room_id=ROOM_ID, date_start=START_DATE, date_end=END_DATE, raise_on_err=True)
    event_list = [*roomevents.items]
    if roomevents.range.total > 500:
        for offset in range(500,roomevents.range.total,500):
            event_list = await dracoon.nodes.get_room_events(room_id=ROOM_ID, date_start=START_DATE, date_end=END_DATE, raise_on_err=True,offset=offset)
            event_list = [*roomevents.items]

    # create CSV in current directory, write header, iterate through results
    with open(fileName, 'w', encoding='utf-8', newline='') as f:
        csv_writer = csv.writer(f, delimiter=',')
        csv_writer.writerow(['id', 'time', 'status', 'operationName', 'message'])

        for LogEvent in event_list:
            if LogEvent.status == 0:
                operation_status = 'Success'
            elif LogEvent.status == 2:
                operation_status = 'Error'

            csv_writer.writerow([LogEvent.id, LogEvent.time, operation_status, LogEvent.operationName, LogEvent.message])

    print(f'CSV room report (room id: {ROOM_ID}) created: ' + fileName)

    await dracoon.logout()


if __name__ == '__main__':
    asyncio.run(main())
