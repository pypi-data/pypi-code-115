import levrt
from levrt import Cr, ctx


def hello() -> Cr:
    @levrt.remote
    def entry():
        ctx.set(msg="Hello, world!")

    return Cr("apline:latest", entry=entry())


async def main():
    doc = await hello()
    data = await doc.get()
    print(data["msg"])


if __name__ == "__main__":
    levrt.run(main())
