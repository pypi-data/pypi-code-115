from typing import List

import datahub.emitter.mce_builder as builder
from datahub.metadata.com.linkedin.pegasus2avro.datajob import DataJobInfoClass
from datahub.metadata.com.linkedin.pegasus2avro.datajob import DataJobInputOutputClass

from dh_client.entities import Entity
from dh_client.entities.glossary_terms import GlossaryTerm
from dh_client.entities.links import Link
from dh_client.entities.owners import Owner
from dh_client.entities.tags import Tag


class DataJob(Entity):
    """
    Examples:

        >>> client.data_job.upsert(flow_id="dag_id", job_id="task_id", run_id="run_id", job_type="airflow", cluster="prod",
        ...                         input_datasets=["dataset_x"], output_datasets=["dataset_y"],
        ...                         external_url="http://url-to.dag", name="Dag Foo", description="A random dag",
        ...                         tags=["airflow"], owners=["Joe"], custom_properties={"a": "1"},
        ...                         glossary_terms=["term_a"], links={"another link": "https://foo.com"},
        ...                         status="FAILED"
        ... )
    """

    entity_type: str = "dataJob"
    aspect_name: str = "dataJobInfo"

    def _create_mpc(
        self,
        flow_id: str = None,
        job_id: str = None,
        run_id: str = None,
        name: str = None,
        env: str = None,
        description: str = None,
        url: str = None,
        tags: List[str] = None,
        owners: List[str] = None,
        custom_properties=None,
        external_url=None,
        glossary_terms: List[str] = None,
        cluster: str = "PROD",
        links: dict = None,
        job_type: str = "airflow",
        status: str = None,
        input_datasets: List[str] = None,
        output_datasets: List[str] = None,
    ) -> List[dict]:
        """Create list of mpc dictionaries for dataset modifications.

        Args:

        Returns:
            a list of mpc dictionaries.
        """
        dataflow_urn = builder.make_data_flow_urn(
            job_type, flow_id=flow_id, cluster=cluster
        )
        datajob_info = DataJobInfoClass(
            name or job_id,
            type=job_type,
            flowUrn=dataflow_urn,
            customProperties=custom_properties,
            externalUrl=external_url,
            description=description,
            status=status,
        )
        datajob_urn = self.create_resource_urn(job_id, flow_id, job_type, cluster)
        mpc = [
            self._create_mpc_dict(
                self.entity_type, datajob_urn, self.aspect_name, datajob_info
            )
        ]

        if tags:
            mpc.append(Tag.create_mpc_association(self.entity_type, datajob_urn, tags))
        if owners:
            mpc.append(
                Owner.create_mpc_association(self.entity_type, datajob_urn, owners)
            )
        if glossary_terms:
            mpc.append(
                GlossaryTerm.create_mpc_association(
                    self.entity_type,
                    datajob_urn,
                    glossary_terms,
                    self.emmiter.datahub_actor,
                )
            )
        if input_datasets and output_datasets:
            mpc.append(
                dict(
                    entityType=self.entity_type,
                    entityUrn=datajob_urn,
                    aspectName="dataJobInputOutput",
                    aspect=DataJobInputOutputClass(
                        inputDatasets=[
                            builder.make_dataset_urn(
                                self.emmiter.dataset_platform,
                                dataset,
                                env or self.emmiter.env,
                            )
                            for dataset in input_datasets
                        ],
                        outputDatasets=[
                            builder.make_dataset_urn(
                                self.emmiter.dataset_platform,
                                dataset,
                                env or self.emmiter.env,
                            )
                            for dataset in output_datasets
                        ],
                    ),
                )
            )
        if links:
            mpc.append(
                Link.create_mpc_association(
                    self.entity_type, datajob_urn, links, self.emmiter.datahub_actor
                )
            )
        return mpc

    @staticmethod
    def create_resource_urn(
        job_id_: str, flow_id_: str, job_type_: str, cluster_: str
    ) -> str:
        """Create the dataset urn.

        Args:
            job_id_: The job id.
            flow_id_: The flow id.
            job_type_: The job type.
            cluster_: The cluster.

        Returns:
            The dataset URN.
        """
        return builder.make_data_job_urn(
            orchestrator=job_type_, flow_id=flow_id_, job_id=job_id_, cluster=cluster_
        )
