import unittest

from dinopy import SamWriter
from dinopy.sambam import AlignmentRecord


class SamWriterTest(unittest.TestCase):
    def test_write_optional_float_array(self):
        """Does writing float arrays work?"""
        record = AlignmentRecord.fromvalues('r003', 2064, 'ref', 29, 17, '6H5M', '*', -1, 0, 'TAGGC', '*',
                                            {'XA': [0.23, -1.43, 0, -4.23e-05]})
        expected_str = "r003\t2064\tref\t30\t17\t6H5M\t*\t0\t0\tTAGGC\t*\tXA:B:f0.23,-1.43,0,-4.23e-05"

        with SamWriter("files/sam_writer_test_float_array.sam", force_overwrite=True) as sw:
            sw.write_record(record)

        with open("files/sam_writer_test_float_array.sam", 'rt') as reader:
            written_record = reader.readline().rstrip()

        self.assertEqual(str(record), written_record)
        self.assertEqual(written_record, expected_str)
        # self.assertEqual(record, AlignmentRecord.fromstr(written_record))  # will fail because of np.ndarray vs python list
        # TODO: find SAM-file that actually describes a float array in its optional columns

    def test_write_optional_uint_array(self):
        """Does writing uint arrays work?"""
        record = AlignmentRecord.fromvalues('r003', 2064, 'ref', 29, 17, '6H5M', '*', -1, 0, 'TAGGC', '*',
                                            {'XB': [23435, 2, 9, 2132432, 34, 42]})
        expected_str = "r003\t2064\tref\t30\t17\t6H5M\t*\t0\t0\tTAGGC\t*\tXB:B:i23435,2,9,2132432,34,42"  # actually XB:B:I not XB:B:i expected, but specification mentions type changes are allowed

        with SamWriter("files/sam_writer_test_uint_array.sam", force_overwrite=True) as sw:
            sw.write_record(record)

        with open("files/sam_writer_test_uint_array.sam", 'rt') as reader:
            written_record = reader.readline().rstrip()

        self.assertEqual(str(record), written_record)
        self.assertEqual(written_record, expected_str)
        # self.assertEqual(record, AlignmentRecord.fromstr(written_record))  # will fail because of np.ndarray vs python list

    def test_write_optional_int_array(self):
        """Does writing int arrays work?"""
        record = AlignmentRecord.fromvalues('r003', 2064, 'ref', 29, 17, '6H5M', '*', -1, 0, 'TAGGC', '*',
                                            {'XC': [-23435, 2, -9, 2132432, 34, -42]})

        with SamWriter("files/sam_writer_test_int_array.sam", force_overwrite=True) as sw:
            sw.write_record(record)

        with open("files/sam_writer_test_int_array.sam", 'rt') as reader:
            written_record = reader.readline().rstrip()

        self.assertEqual(str(record), written_record)
        # self.assertEqual(record, AlignmentRecord.fromstr(written_record))  # will fail because of np.ndarray vs python list

    def test_write_optional_hexarray_1(self):
        """Does writing byte-/hexarrays work? (from bytes)"""
        record = AlignmentRecord.fromvalues('r003', 2064, 'ref', 29, 17, '6H5M', '*', -1, 0, 'TAGGC', '*',
                                            {'XD': b'\x01\xff\x03'})

        with SamWriter("files/sam_writer_test_hexarray1.sam", force_overwrite=True) as sw:
            sw.write_record(record)

        with open("files/sam_writer_test_hexarray1.sam", 'rt') as reader:
            written_record = reader.readline().rstrip()

        self.assertEqual(str(record), written_record)
        self.assertEqual(record, AlignmentRecord.fromstr(written_record))

    def test_write_optional_hexarray_2(self):
        """Does writing byte-/hexarrays work? (from bytearray)"""
        record = AlignmentRecord.fromvalues('r003', 2064, 'ref', 29, 17, '6H5M', '*', -1, 0, 'TAGGC', '*',
                                            {'XE': bytearray([1, 45, 255, 32])})

        with SamWriter("files/sam_writer_test_hexarray2.sam", force_overwrite=True) as sw:
            sw.write_record(record)

        with open("files/sam_writer_test_hexarray2.sam", 'rt') as reader:
            written_record = reader.readline().rstrip()

        self.assertEqual(str(record), written_record)
        self.assertEqual(record, AlignmentRecord.fromstr(written_record))

    def test_write_record(self):
        """Does the SamReader correctly read and parse an AlignmentRecord from a SAM-file? (compared to manually defining AlignmentRecord.fromdict...)"""
        record = AlignmentRecord.fromdict(
            {'query_name': 'r001', 'flag': 99, 'rname': 'ref', 'pos': 7, 'mapping_quality': 30, 'cigar': '8M2I4M1D3M',
             'rnext': '=', 'pnext': 37, 'template_length': 39, 'query_sequence': 'TTAGATAAAGGATACTG', 'qual': '*',
             'optional': None})

        with SamWriter("files/sam_writer_test_single_record.sam", force_overwrite=True) as sw:
            sw.write_record(record)

        with open("files/sam_writer_test_single_record.sam", 'rt') as reader:
            written_record = reader.readline().rstrip()
        self.assertEqual(str(record), written_record)
        self.assertEqual(record, AlignmentRecord.fromstr(written_record))

    def test_write_sam(self):
        """Does the SamWriter correctly write AlignmentRecords to a SAM-file? 1"""
        records = [
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

        with SamWriter("files/sam_writer_test_1.sam", force_overwrite=True) as sw:
            sw.write_records(records)

        with open("files/sam_writer_test_1.sam", 'rt') as reader:
            written_records = reader.readlines()
        self.assertListEqual(list(map(str, records)), list(map(str.rstrip, written_records)))
        self.assertListEqual(records, list(map(AlignmentRecord.fromstr, written_records)))

        expected_file_contents = "r001	99	ref	7	30	8M2I4M1D3M	=	37	39	TTAGATAAAGGATACTG	*\nr002	0	ref	9	30	3S6M1P1I4M	*	0	0	AAAAGATAAGGATA	*\nr003	0	ref	9	30	5S6M	*	0	0	GCCTAAGCTAA	*	SA:Z:ref,29,-,6H5M,17,0;\nr004	0	ref	16	30	6M14N5M	*	0	0	ATAGCTTCAGC	*\nr003	2064	ref	29	17	6H5M	*	0	0	TAGGC	*	SA:Z:ref,9,+,5S6M,30,1;\nr001	147	ref	37	30	9M	=	7	-39	CAGCGGCAT	*	NM:i:1\n"
        self.assertEqual(expected_file_contents, "".join(written_records))

    def test_write_sam2(self):
        """Does the SamWriter correctly write AlignmentRecords to a SAM-file? 2"""
        records = [
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
        with SamWriter("files/sam_writer_test_2.sam", force_overwrite=True) as sw:
            sw.write_records(records)

        with open("files/sam_writer_test_2.sam", 'rt') as reader:
            written_records = reader.readlines()
        self.assertListEqual(list(map(str, records)), list(map(str.rstrip, written_records)))
        self.assertListEqual(records, list(map(AlignmentRecord.fromstr, written_records)))

        expected_file_contents = "r001	99	ref	7	30	8M2I4M1D3M	=	37	39	TTAGATAAAGGATACTG	*\nr002	0	ref	9	30	3S6M1P1I4M	*	0	0	AAAAGATAAGGATA	*\nr003	0	ref	9	30	5S6M	*	0	0	GCCTAAGCTAA	*	SA:Z:ref,29,-,6H5M,17,0;\nr004	0	ref	16	30	6M14N5M	*	0	0	ATAGCTTCAGC	*\nr003	2064	ref	29	17	6H5M	*	0	0	TAGGC	*	SA:Z:ref,9,+,5S6M,30,1;\nr001	147	ref	37	30	9M	=	7	-39	CAGCGGCAT	*	NM:i:1\n"
        self.assertEqual(expected_file_contents, "".join(written_records))


if __name__ == "__main__":
    unittest.main()
