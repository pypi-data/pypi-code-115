import env
from dcclab import *
import unittest

class TestTimeSeries(env.DCCLabTestCase):

    def testInit(self):
        self.assertIsNotNone(TimeSeries())

    def testInitWithPattern(self):
        self.assertIsNotNone(TimeSeries(pathPattern= "{0}/test-(\d+).jpg".format(self.dataDir)))

    def testInitWithImageData(self):
        imageData = np.random.randint(low=0, high=255, size=(100, 200,3,10))
        series = TimeSeries(imagesArray=imageData)
        self.assertIsNotNone(series)
        self.assertEqual(series.numberOfImages, 10)

    def testSeriesAsArray(self):
        series = TimeSeries(pathPattern= "{0}/test-(\d+).jpg".format(self.dataDir))
        self.assertTrue(len(series.images) > 0)
        array = series.asArray()
        self.assertIsNotNone(array)

    def testSeriesSave(self):
        imageData = np.random.randint(low=0, high=255, size=(100, 200,3,10))
        series = TimeSeries(imagesArray=imageData)
        series.save("/tmp/testWrite-{0:03d}.tif")

        pattern = PathPattern("/tmp/testWrite-{0:03d}.tif")
        for i in range(10):
            file = pattern.filePathWithIndex(i)
            self.assertTrue(os.path.exists(file),"{0} does not exist".format(file))

    def testSeriesSave(self):
        imageData = np.random.randint(low=0, high=255, size=(100, 200,3,10))
        series = TimeSeries(imagesArray=imageData)
        series.save("/tmp/test.avi")
        self.assertTrue(os.path.exists("/tmp/test.avi"))

if __name__ == '__main__':
    unittest.main()
