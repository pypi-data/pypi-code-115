import asyncio
from datetime import timedelta

from runbox import DockerExecutor
from runbox.models import (
    DockerProfile, Limits, File
)
from runbox.testing import IOTestCase, BaseTestSuite

profile = DockerProfile(
    image='python-sandbox:latest',
    workdir_mount='/sandbox',
    exec='python',
    user='sandbox'
)

limits = Limits(
    time=timedelta(seconds=3),
    memory_mb=64,
)

content = """
# FizzBuzz

n = int(input())

if n % 3 == 0 and n % 5 == 0:
    print("FizzBuzz")
elif n % 3 == 0:
    print("Fizz")
elif n % 5 == 0:
    print("Buzz")
else:
    print(n)
"""

file = File(name='main.py', content=content)


async def main():
    test_suite = BaseTestSuite(profile, limits, [file])
    test_suite.add_tests(
        IOTestCase(b'15\n', b'FizzBuzz\n'),
        IOTestCase(b'9\n', b'Fizz\n'),
        IOTestCase(b'13\n', b'13\n'),
        IOTestCase(b'25\n', b'Buzz\n'),
        IOTestCase(b'not a number\n', b'anything\n')
    )

    executor = DockerExecutor()
    result = await test_suite.exec(executor)

    await executor.close()
    print(*result, sep='\n')


if __name__ == '__main__':
    asyncio.run(main())
