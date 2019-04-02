from sqlalchemy import *
from Database import engine

conn = engine.connect()


def show_salary_statistics():
    query = '''select max(sal_to) as max from vacancy'''
    cursor = conn.execute(text(query))
    max_sal = 0
    for row in cursor:
        max_sal = row.max
        break
    segment = 5
    frac = max_sal / segment + 1
    low_sal = 1
    num = []
    sal_range = []
    for i in range(segment):
        low_sal = low_sal
        high_sal = low_sal + frac
        query = '''select count(*) as num from vacancy where sal_to >''' + str(low_sal)+ ' and ' + 'sal_to < ' + str(high_sal)
        cursor = conn.execute(text(query))
        for row in cursor:
            num.append(int(row.num))
            sal_range.append('Salary from: ' + str(low_sal) + ' to ' + str(high_sal))
            break
        low_sal = high_sal + 1
    numsum = float(sum(num))
    for i in range(len(num)):
        num[i] = float(num[i]) / float(numsum) * 100
    return num, sal_range

