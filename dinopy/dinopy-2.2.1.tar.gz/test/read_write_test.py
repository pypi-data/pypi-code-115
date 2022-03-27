# -*- coding: utf-8 -*-
import unittest

import dinopy
from dinopy import FastaReader, FastaWriter
from dinopy.definitions import FastaEntryC

REFERENCE_PATH_FASTA = "files/testgenome.fasta"
REFERENCE_PATH_FASTA_ZIPPED = "files/testgenome.fasta.gz"
REFERENCE_PATH_FASTA_IUPAC = "files/testgenome_IUPAC.fasta"

REFERENCE_PATH_FASTQ = "files/testreads.fastq"
REFERENCE_PATH_FASTQ_ZIPPED = "files/testreads.fastq.gz"


class TestReadWriteFasta(unittest.TestCase):

    def test_read_write_read_entries(self):
        """Read in entries from file using FastaReader, write using FastaWriter, compare original file to file written by dinopy
        """
        far = FastaReader(REFERENCE_PATH_FASTA)
        entries = list(far.entries())
        tmp_path = "testgenome.dinopy.fasta"
        with FastaWriter(tmp_path, force_overwrite=True) as faw:
            faw.write_entries(entries)

        far2 = FastaReader(tmp_path)
        entries2 = list(far2.entries())
        self.assertEqual(entries, entries2)

    def test_read_write_read_entries_keep_linewidth(self):
        """Read in entries from file using FastaReader, write using FastaWriter, compare original file to file written by dinopy
        """
        far = FastaReader(REFERENCE_PATH_FASTA)
        line_width = far._guess_line_length() - 1  # _guess_line_length returns the number of *bytes* including *newline*
        entries = list(far.entries())
        tmp_path = "testgenome.dinopy.fasta"
        with FastaWriter(tmp_path, force_overwrite=True, line_width=line_width) as faw:
            faw.write_entries(entries)

        file1_lines = []
        for line in open(REFERENCE_PATH_FASTA, 'rb'):
            file1_lines.append(line)
        file1_data = b''.join(file1_lines)

        file2_lines = []
        for line in open(tmp_path, 'rb'):
            file2_lines.append(line)
        file2_data = b''.join(file2_lines)
        self.assertEqual(file1_data, file2_data)

    def test_write_read_entries(self):
        entry1 = FastaEntryC(b'ACGT' * 32, b'chromosome_I', 128, (0, 128))
        entry2 = FastaEntryC(b'CGTA' * 32, b'chromosome_II', 128, (128, 256))
        tmp_path = "test_write_read_write_entries.fasta"
        with FastaWriter(tmp_path, force_overwrite=True) as faw:
            faw.write_entry(entry1)
            faw.write_entry(entry2)

        far = FastaReader(tmp_path)
        entries = list(far.entries())
        self.assertListEqual(entries, [entry1, entry2])

    def test_read_write_genome(self):
        """Read in a genome from file using FastaReader, write using FastaWriter, compare original file to file written by dinopy
        """
        far = FastaReader(REFERENCE_PATH_FASTA)
        genome = far.genome()
        tmp_path = "testgenome.dinopy.fasta"
        with FastaWriter(tmp_path, force_overwrite=True) as faw:
            faw.write_genome(genome)

        with FastaWriter(tmp_path, force_overwrite=True) as faw:
            faw.write_genome(*genome)

        far2 = FastaReader(tmp_path)
        genome2 = far2.genome()
        self.assertEqual(genome, genome2)


class TestReadWriteFastq(unittest.TestCase):

    def test_read_write_read(self):
        """Read in a Fastq file read-wise, write back using FastqWriter.
        Note that this will fail, as both FastqReader and FastqWriter discard
        plus-line information."""
        fqr = dinopy.FastqReader(REFERENCE_PATH_FASTQ)
        tmp_path = "testreads.dinopy.fastq"
        with dinopy.FastqWriter(tmp_path, force_overwrite=True) as fqw:
            fqw.write_reads(fqr.reads())

        file1_lines = []
        for line in open(REFERENCE_PATH_FASTQ, 'rb'):
            file1_lines.append(line)
        file1_data = b''.join(file1_lines)

        file2_lines = []
        for line in open(tmp_path, 'rb'):
            file2_lines.append(line)
        file2_data = b''.join(file2_lines)
        with self.assertRaises(AssertionError):  # TODO: handle this properly.
            self.assertEqual(file1_data, file2_data)


if __name__ == "__main__":
    unittest.main()
