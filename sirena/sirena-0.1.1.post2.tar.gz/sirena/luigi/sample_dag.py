from typing import Optional
from sirena.flowchart.shapes import FlowChart,Symbol,FlowChartEdge

import luigi
from random import randint

class GrandParent(luigi.Task):
    pass

class ParentTask(luigi.Task):

    def requires(self):
        return [GrandParent()]

class UncleTask(luigi.Task):

    def requires(self):
        return [GrandParent()]

class Aunties(luigi.Task):
    number = luigi.IntParameter()

    def requires(self):
        return [GrandParent()]


class Child(luigi.Task):

    def requires(self):


        aunts = [Aunties(i) for i in range(10)]
        return [ParentTask(),UncleTask(),*aunts]


def get_edges_items(task: luigi.Task):

    items = [Symbol(id=task.task_id)]

    for t in task.deps():
        items.append(FlowChartEdge(end=Symbol(id=task.task_id),start=Symbol(id=t.task_id)))
        _i= get_edges_items(t)
        items.extend(_i)
    return items


def build_task_tree(task):
    items = get_edges_items(task)

    return FlowChart(items=items)
