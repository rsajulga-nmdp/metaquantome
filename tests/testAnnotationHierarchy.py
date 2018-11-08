import unittest
import pandas as pd
from metaquantome.AnnotationNode import AnnotationNode
from metaquantome.AnnotationHierarchy import AnnotationHierarchy
from metaquantome.databases.NCBITaxonomyDb import NCBITaxonomyDb
from metaquantome.databases.GeneOntologyDb import GeneOntologyDb
from metaquantome.databases.EnzymeDb import EnzymeDb
from metaquantome.util.utils import define_ontology_data_dir


class TestAnnotationHierarchyNcbi(unittest.TestCase):
    ddir = define_ontology_data_dir('taxonomy')

    def _create_sapiens_db(self):
        db = NCBITaxonomyDb(self.ddir)
        sample_set = {9604, 9605, 9606}  # hominidae (family), homo (genus), homo sapiens (species)
        ah = AnnotationHierarchy(db, sample_set, 'samp1')
        return ah, sample_set

    def testInit(self):
        ah, sample_set = self._create_sapiens_db()
        self.assertIsInstance(ah.db, NCBITaxonomyDb)
        self.assertSetEqual(ah.sample_set, sample_set)
        self.assertDictEqual(ah.nodes, dict())

    def testUpdateNode(self):
        ah, sample_set = self._create_sapiens_db()
        # one sample child
        testid = 9605
        intensity = 200
        ah._add_node(testid, intensity)
        ah._define_sample_children()
        updated_node = ah.nodes[testid]
        self.assertIsInstance(updated_node, AnnotationNode)
        self.assertEqual(updated_node.intensity, intensity)
        self.assertEqual(updated_node.n_sample_children, 1)

    def testAggregateNodes(self):
        ah, sample_set = self._create_sapiens_db()
        testids = [9604, 9605, 9606]
        test_intensities = [500, 200, 300]
        for i in range(0, 3):
            ah._add_node(testids[i], test_intensities[i])
        self.assertEqual(ah.nodes[9604].intensity, 1000)

    # def testGetInformativeNodes(self):
    #     db = NCBITaxonomyDb(self.ddir)
    #     sample_set = {9604, 9605, 9606, 9599}  # hominidae (family), homo (genus), homo sapiens (species)
    #     ah = AnnotationHierarchy(db, sample_set, 'samp1')
    #     # we have hominidae, homo, homo sapiens, and pongo (genus)
    #     testids = [9604, 9605, 9606, 9599, 9604, 9606, 9599]
    #     # intensity is not important here
    #     test_intensity = 1
    #
    #     exp_ancestors = set(testids)
    #     for id in testids:
    #         ah.add_node(id, test_intensity)
    #         exp_ancestors.update(db.get_ancestors(id))
    #
    #     # filter without any actual filtering
    #     ah.get_informative_nodes(min_peptides=0, min_children_non_leaf=0)
    #     # we expect that all remain, plus the ancestors
    #
    #     self.assertSetEqual(set(ah.informative_nodes.keys()), exp_ancestors)
    #
    #     # real filtering
    #     ah.get_informative_nodes(min_peptides=2, min_children_non_leaf=2)
    #     # we expect that the only ones remaining are 9604, 9606, and 9599
    #     self.assertSetEqual(set(ah.informative_nodes.keys()), {9604, 9606, 9599})


class TestAnnotationHierarchyGO(unittest.TestCase):
    ddir = define_ontology_data_dir('go')
    def _create_go_db(self):
        db = GeneOntologyDb(self.ddir)
        sample_set = {'GO:0008150',  # biological process
                      'GO:0008283',  # cell proliferation (child of BP)
                      'GO:0033687',  # osteoblast proliferation (child of cell pro)
                      'GO:0036093',  # germ cell proliferation (child of cell pro)
                      'GO:0022414',  # reproductive process (child of BP)
                      'GO:1903046',  # meiotic cell cycle process (child of rep pro)
                      'GO:0051026'}  # chiasma assembly, child of meiotic
        ah = AnnotationHierarchy(db, sample_set, 'samp1')
        return ah, sample_set

    def testInit(self):
        ah, sample_set = self._create_go_db()
        self.assertIsInstance(ah.db, GeneOntologyDb)
        self.assertSetEqual(ah.sample_set, sample_set)
        self.assertDictEqual(ah.nodes, dict())

    def testUpdateNode(self):
        ah, sample_set = self._create_go_db()
        # one sample child
        testid = 'GO:0051026'
        intensity = 100
        ah._add_node(testid, intensity)
        updated_node = ah.nodes[testid]
        self.assertIsInstance(updated_node, AnnotationNode)
        self.assertEqual(updated_node.intensity, intensity)
        ah._define_sample_children()
        self.assertEqual(updated_node.n_sample_children, 0)

    def testAggregateNodes(self):
        ah, sample_set = self._create_go_db()
        testids = ['GO:0008150',  # biological process
                   'GO:0008283',  # cell proliferation (child of BP)
                   'GO:0033687',  # osteoblast proliferation (child of cell pro)
                   'GO:0036093',  # germ cell proliferation (child of cell pro and rep pro)
                   'GO:0022414',  # reproductive process (child of BP)
                   'GO:1903046',  # meiotic cell cycle process (child of rep pro)
                   'GO:0051026']  # chiasma assembly, child of meiotic
        test_intensities = [0, 0, 0, 100, 50, 200, 300]
        for i in range(0, len(test_intensities)):
            ah._add_node(testids[i], test_intensities[i])
        self.assertEqual(ah.nodes['GO:0022414'].intensity, 650)

    # def testGetInformativeNodes(self):
    #     ah, sample_set = self._create_go_db()
    #     db = ah.db
    #     testids = ['GO:0008150',  # biological process
    #                'GO:0008150',  # repeat
    #                'GO:0008283',  # cell proliferation (child of BP)
    #                'GO:0033687',  # osteoblast proliferation (child of cell pro)
    #                'GO:0036093',  # germ cell proliferation (child of cell pro and rep pro)
    #                'GO:0036093',  # repeat
    #                'GO:0022414',  # reproductive process (child of BP)
    #                'GO:0022414',  # repeat
    #                'GO:1903046',  # meiotic cell cycle process (child of rep pro)
    #                'GO:0051026',  # chiasma assembly, child of meiotic
    #                'GO:0051026']  # repeat
    #     # intensity is not important here
    #     test_intensity = 1
    #
    #     exp_ancestors = set(testids)
    #     for id in testids:
    #         ah.add_node(id, test_intensity)
    #         exp_ancestors.update(db.get_ancestors(id))
    #
    #     # filter without any actual filtering
    #     ah.get_informative_nodes(min_peptides=0, min_children_non_leaf=0)
    #     # we expect that all remain
    #     self.assertSetEqual(exp_ancestors, set(ah.informative_nodes.keys()))
    #
    #     # real filtering
    #     # the nodes with 2+ children are:
    #     # bio process ('GO:0008150')
    #     # reproductive process ('GO:0022414')
    #     # the leaves are:
    #     # chiasma assembly ('GO:0051026')
    #     # germ cell prolif ('GO:0036093')
    #     # all of these have 2 peptides
    #     # then we also get GO:0009987, cellular process, and
    #     # GO:0002823, cell proliferaction
    #     ah.get_informative_nodes(min_peptides=2, min_children_non_leaf=2)
    #     self.assertSetEqual(set(ah.informative_nodes.keys()),
    #                         {'GO:0008150', 'GO:0022414', 'GO:0051026', 'GO:0036093', 'GO:0009987', 'GO:0008283'})


class TestAnnotationHierarchyEc(unittest.TestCase):
    ddir = define_ontology_data_dir('ec')

    def _create_ec_db(self):
        db = EnzymeDb(self.ddir)
        sample_set = {'1.1.4.-',
                      '1.1.4.1',
                      '1.1.4.2',
                      '6.5.-.-',
                      '6.-.-.-'}
        ah = AnnotationHierarchy(db, sample_set, 'samp1')
        return ah, sample_set

    def testInit(self):
        ah, sample_set = self._create_ec_db()
        self.assertIsInstance(ah.db, EnzymeDb)
        self.assertSetEqual(ah.sample_set, sample_set)
        self.assertDictEqual(ah.nodes, dict())

    def testUpdateNode(self):
        ah, sample_set = self._create_ec_db()
        # one sample child
        testid = '1.1.4.-'
        intensity = 100
        ah._add_node(testid, intensity)
        updated_node = ah.nodes[testid]
        ah._define_sample_children()
        self.assertIsInstance(updated_node, AnnotationNode)
        self.assertEqual(updated_node.intensity, intensity)
        self.assertEqual(updated_node.n_sample_children, 2)

    def testAggregateNodes(self):
        ah, sample_set = self._create_ec_db()
        testids = ['1.1.4.-',
                   '1.1.4.1',
                   '1.1.4.2',
                   '6.5.-.-']
        test_intensities = [500, 200, 300, 0]
        for i in range(0, 3):
            ah._add_node(testids[i], test_intensities[i])
        self.assertEqual(ah.nodes['1.1.4.-'].intensity, 1000)

    # def testGetInformativeNodes(self):
    #     ah, sample_set = self._create_ec_db()
    #     test_set = ['1.1.4.-',
    #                 '1.1.4.1',
    #                 '1.1.4.2',
    #                 '1.1.4.-',
    #                 '1.1.4.1',
    #                 '1.1.4.2',
    #                 '6.5.-.-',
    #                 '6.5.-.-',
    #                 '6.-.-.-',
    #                 '6.-.-.-']
    #     # intensity is not important here
    #     test_intensity = 1
    #     for id in test_set:
    #         ah.add_node(id, test_intensity)
    #
    #     # filter without any actual filtering
    #     ah.define_sample_children()
    #     # we expect that all remain, plus 1.1.-.- and 1.-.-.-
    #     self.assertSetEqual(set(ah.informative_nodes.keys()), {'1.1.4.-',
    #                                             '1.1.4.1',
    #                                             '1.1.4.2',
    #                                             '6.5.-.-',
    #                                             '6.-.-.-',
    #                                             '1.1.-.-',
    #                                             '1.-.-.-'})
    #     # real filtering
    #     info1 = ah.get_informative_nodes(min_peptides=2, min_children_non_leaf=2)
    #     # we expect that the only ones remaining are 1.1.4.- and 6.5.-.-
    #     self.assertSetEqual(set(ah.informative_nodes.keys()), {'1.1.4.-',
    #                                             '1.1.4.1',
    #                                             '1.1.4.2',
    #                                             '6.5.-.-',})

    def testToDataframe(self):
        ah, sample_set = self._create_ec_db()
        test_set = ['1.1.4.-',
                    '1.1.4.1',
                    '1.1.4.2',
                    '1.1.4.-',
                    '1.1.4.1',
                    '1.1.4.2',
                    '6.5.-.-',
                    '6.5.-.-',
                    '6.-.-.-',
                    '6.-.-.-']
        # set to one, so it's equal to number of peptides
        test_intensity = 1
        for id in test_set:
            ah._add_node(id, test_intensity)

        ah._define_sample_children()

        # the sample set is as below:
        #         sample_set = {'1.1.4.-',
        #                       '1.1.4.1',
        #                       '1.1.4.2',
        #                       '6.5.-.-',
        #                       '6.-.-.-'}
        # ah.get_informative_nodes(0, 0)
        # expected
        exp_df = pd.DataFrame({'samp1': [6, 6, 6, 2, 2, 4, 2],
                               'samp1_n_peptide': [6, 6, 6, 2, 2, 4, 2],
                               'samp1_n_samp_children': [1, 1, 2, 0, 0, 1, 0]},
                               index= ['1.-.-.-',
                                       '1.1.-.-',
                                       '1.1.4.-',
                                       '1.1.4.1',
                                       '1.1.4.2',
                                       '6.-.-.-',
                                       '6.5.-.-']).sort_index()
        df = ah.to_dataframe().sort_index()
        self.assertTrue(df.equals(exp_df))


if __name__ == '__main__':
    unittest.main()
