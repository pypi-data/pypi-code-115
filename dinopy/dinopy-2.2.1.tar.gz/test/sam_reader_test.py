import unittest

from dinopy import SamReader
from dinopy.sambam import AlignmentRecord


class SamReaderTest(unittest.TestCase):
    def test_read_header(self):
        sr = SamReader("files/example.sam")
        header = sr.get_header()
        expected_header = [('@HD', {'SO': 'coordinate', 'VN': '1.5'}), ('@SQ', {'SN': 'ref', 'LN': '45'})]
        self.assertListEqual(header, expected_header)

    def test_read_record(self):
        """Does the SamReader correctly read and parse an AlignmentRecord from a SAM-file? (compared to manually defining AlignmentRecord.fromdict...)"""
        expected_record = AlignmentRecord.fromdict(
            {'query_name': 'r001', 'flag': 99, 'rname': 'ref', 'pos': 6, 'mapping_quality': 30, 'cigar': '8M2I4M1D3M',
             'rnext': '=', 'pnext': 36, 'template_length': 39, 'query_sequence': 'TTAGATAAAGGATACTG', 'qual': '*',
             'optional': None})

        sr = SamReader("files/example.sam")
        _ = sr.get_header()
        record = list(sr.records())[0]
        self.assertEqual(expected_record, record)

    def test_read_sam2(self):
        """Does the SamReader correctly read and parse AlignmentRecords from a SAM-file? (compared to manually defining AlignmentRecord.fromvalues...)"""
        expected_records = [
            AlignmentRecord.fromvalues('r001', 99, 'ref', 6, 30, '8M2I4M1D3M', '=', 36, 39, 'TTAGATAAAGGATACTG', '*',
                                       None),
            AlignmentRecord.fromvalues('r002', 0, 'ref', 8, 30, '3S6M1P1I4M', '*', -1, 0, 'AAAAGATAAGGATA', '*', None),
            AlignmentRecord.fromvalues('r003', 0, 'ref', 8, 30, '5S6M', '*', -1, 0, 'GCCTAAGCTAA', '*',
                                       {'SA': 'ref,29,-,6H5M,17,0;'}),
            AlignmentRecord.fromvalues('r004', 0, 'ref', 15, 30, '6M14N5M', '*', -1, 0, 'ATAGCTTCAGC', '*', None),
            AlignmentRecord.fromvalues('r003', 2064, 'ref', 28, 17, '6H5M', '*', -1, 0, 'TAGGC', '*',
                                       {'SA': 'ref,9,+,5S6M,30,1;'}),
            AlignmentRecord.fromvalues('r001', 147, 'ref', 36, 30, '9M', '=', 6, -39, 'CAGCGGCAT', '*', {'NM': 1})
        ]

        sr = SamReader("files/example.sam")
        _ = sr.get_header()
        records = list(sr.records())
        self.assertListEqual(expected_records, records)

    def test_sam3(self):
        """Does the SamReader correctly read and parse AlignmentRecords from a SAM-file? (compared to manually defining AlignmentRecord.fromstr...)"""
        sr = SamReader("files/example.sam")
        _ = sr.get_header()
        expected_records = [
            AlignmentRecord.fromstr(
                "r001	99	ref	7	30	8M2I4M1D3M	=	37	39	TTAGATAAAGGATACTG	*"),
            AlignmentRecord.fromstr("r002	0	ref	9	30	3S6M1P1I4M	*	0	0	AAAAGATAAGGATA	*"),
            AlignmentRecord.fromstr(
                "r003	0	ref	9	30	5S6M	*	0	0	GCCTAAGCTAA	*	SA:Z:ref,29,-,6H5M,17,0;"),
            AlignmentRecord.fromstr("r004	0	ref	16	30	6M14N5M	*	0	0	ATAGCTTCAGC	*"),
            # mixed escaped and non-escaped tabs
            AlignmentRecord.fromstr(
                "r003\t2064	ref	29	17	6H5M\t*\t0	0	TAGGC	*	SA:Z:ref,9,+,5S6M,30,1;"),
            # escaped tabs
            AlignmentRecord.fromstr("r001\t147\tref\t37\t30\t9M\t=\t7\t-39\tCAGCGGCAT\t*\tNM:i:1")
        ]
        records = list(sr.records())
        self.assertListEqual(expected_records, records)

    def test_sam_string_representation(self):
        sr = SamReader("files/example.sam")
        _ = sr.get_header()
        expected_records = [
            "r001	99	ref	7	30	8M2I4M1D3M	=	37	39	TTAGATAAAGGATACTG	*",
            "r002	0	ref	9	30	3S6M1P1I4M	*	0	0	AAAAGATAAGGATA	*",
            "r003	0	ref	9	30	5S6M	*	0	0	GCCTAAGCTAA	*	SA:Z:ref,29,-,6H5M,17,0;",
            "r004	0	ref	16	30	6M14N5M	*	0	0	ATAGCTTCAGC	*",
            "r003	2064	ref	29	17	6H5M	*	0	0	TAGGC	*	SA:Z:ref,9,+,5S6M,30,1;",
            "r001	147	ref	37	30	9M	=	7	-39	CAGCGGCAT	*	NM:i:1"
        ]
        records = list(map(str, sr.records()))
        self.assertListEqual(expected_records, records)


if __name__ == "__main__":
    unittest.main()
