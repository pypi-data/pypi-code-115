from . import WMLDeployment

class MulticlassIrisSpark(WMLDeployment):
    def __init__(self,facts_client,is_cp4d:bool=False):
        super (MulticlassIrisSpark,self).__init__(name="Spark Iris",
            asset_name="Spark Iris",facts_client=facts_client,is_cp4d=is_cp4d)

    def train_model(self):
        import pyspark
        from pyspark.sql import SparkSession
        from pyspark.ml.classification import LogisticRegression
        from pyspark.ml.feature import VectorAssembler
        from pyspark.sql import SparkSession
        from sklearn.datasets import load_iris
        from pyspark.ml.evaluation import (
            MulticlassClassificationEvaluator

        )

        spark=SparkSession.builder.getOrCreate()
        # spark = (SparkSession.builder
        #     .config("spark.jars.packages", self.facts_client.ORG_FACTS_SPARK) # using variable option
        #     .getOrCreate())


        df = load_iris(as_frame=True).frame.rename(columns={"target": "label"})
        df = spark.createDataFrame(df)
        df = VectorAssembler(inputCols=df.columns[:-1], outputCol="features").transform(df)
        train, test = df.randomSplit([0.8, 0.2])

        lor = LogisticRegression(maxIter=5)

        lorModel = lor.fit(train)

        mce = MulticlassClassificationEvaluator(metricName="logLoss")
        pred_result = lorModel.transform(test)
        logloss = mce.evaluate(pred_result)

        accuracy = mce.evaluate(pred_result, params={mce.metricName: "accuracy"})

        self.facts_client.export_facts.export_payload(self.facts_client.runs.get_current_run_id())

        spark.stop()



class MulticlassIrisSparkPipeline(WMLDeployment):
    def __init__(self,facts_client,is_cp4d:bool=False):
        super (MulticlassIrisSparkPipeline,self).__init__(name="Spark Iris pipeline",
            asset_name="Spark Iris pipeline",facts_client=facts_client,is_cp4d=is_cp4d)

    def train_model(self):

        import pyspark
        from pyspark.ml.classification import LogisticRegression
        from pyspark.ml.feature import VectorAssembler, StandardScaler
        from pyspark.ml import Pipeline
        from pyspark.sql import SparkSession
        from sklearn.datasets import load_iris
        from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
        from pyspark.ml.evaluation import BinaryClassificationEvaluator,MulticlassClassificationEvaluator

        spark=SparkSession.builder.getOrCreate()

        # spark = (SparkSession.builder
        #     .config("spark.jars.packages", self.facts_client.ORG_FACTS_SPARK) # using variable option
        #     .getOrCreate())


        df = load_iris(as_frame=True).frame.rename(columns={"target": "label"})
        df = spark.createDataFrame(df)
        train, test = df.randomSplit([0.8, 0.2])

        assembler = VectorAssembler(inputCols=df.columns[:-1], outputCol="features")
        scaler = StandardScaler(inputCol=assembler.getOutputCol(), outputCol="scaledFeatures")
        lor = LogisticRegression(maxIter=5, featuresCol=scaler.getOutputCol())

        # Non-neseted pipeline
        pipeline = Pipeline(stages=[assembler, scaler, lor])

        paramGrid = ParamGridBuilder()\
        .addGrid(lor.maxIter, [100])\
        .addGrid(lor.elasticNetParam, [0.0, 1.0]).build()
        #.addGrid(lor.fitIntercept, [True, False])\
        #.build()

        crossValidator = CrossValidator(estimator=pipeline, estimatorParamMaps=paramGrid,
                                    evaluator=MulticlassClassificationEvaluator(metricName="weightedPrecision"))

        pipeline_model = crossValidator.fit(train)

        spark.stop()