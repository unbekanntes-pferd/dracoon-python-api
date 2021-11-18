"""
Example script showing the new async API and the creation of reports

04.11.2021 Octavio Simone

"""

from dracoon import DRACOON

import asyncio

async def main():
    baseURL = 'https://dracoon.team'
    client_id = 'XXXXXXXXXXXXXXXXXXXXXX'
    client_secret = 'XXXXXXXXXXXXXXXXXXXXXXXXXXX'

    dracoon = DRACOON(base_url=baseURL, client_id=client_id, client_secret=client_secret)

    await dracoon.connect()

    report = {
	"name": "Audit Log Report",
	"type": "single",
	"subType": "general-audit-report",
	"formats": ["csv-plain"],
	"enabled": True,
	"target": {
		"id": 8533
	}
}

    res = await dracoon.reports.create_report(report)

    print(res)

    await dracoon.logout()

if __name__ == '__main__':
    asyncio.run(main())