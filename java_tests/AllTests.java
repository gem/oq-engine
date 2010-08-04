/*
 * [COPYRIGHT]
 *
 * [NAME] is free software; you can redistribute it and/or modify it
 * under the terms of the GNU Lesser General Public License as
 * published by the Free Software Foundation; either version 2.1 of
 * the License, or (at your option) any later version.
 *
 * This software is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this software; if not, write to the Free
 * Software Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA
 * 02110-1301 USA, or see the FSF site: http://www.fsf.org.
 */

import org.gem.engine.calc.ConditionalLossTest;
import org.gem.engine.calc.InterpolatorTest;
import org.gem.engine.calc.IntervalTest;
import org.gem.engine.calc.LossCurveTest;
import org.gem.engine.calc.LossRatioCurveTest;
import org.gem.engine.calc.LossRatioExceedanceMatrixProbOccTest;
import org.gem.engine.calc.LossRatioExceedanceMatrixSegmentationTest;
import org.gem.engine.calc.LossRatioExceedanceMatrixTest;
import org.gem.engine.calc.LossRatioMeanTest;
import org.gem.engine.calc.LossRatioStdDevTest;
import org.gem.engine.calc.MeanLossTest;
import org.gem.engine.calc.ProbabilityOfOccurrenceTest;
import org.gem.engine.core.event.listener.AssetLoaderTest;
import org.gem.engine.core.event.listener.CountryLoaderTest;
import org.gem.engine.core.event.listener.DiscreteVulnerabilityFunctionKeyCacheLoaderTest;
import org.gem.engine.core.event.listener.DiscreteVulnerabilityFunctionKeyCacheSynchronizerTest;
import org.gem.engine.core.event.listener.DiscreteVulnerabilityFunctionLoaderTest;
import org.gem.engine.core.event.listener.ValidatorTest;
import org.gem.engine.core.event.listener.det.DeterministicScenarioCacheKeyTest;
import org.gem.engine.core.event.listener.det.DeterministicScenarioCacheLoaderTest;
import org.gem.engine.core.event.listener.det.DeterministicScenarioCacheSynchronizerTest;
import org.gem.engine.core.event.listener.det.DistributionLoaderTest;
import org.gem.engine.core.event.listener.det.HazardIMLLoaderTest;
import org.gem.engine.core.event.listener.det.HazardIMLRounderTest;
import org.gem.engine.core.event.listener.det.LossCalculatorTest;
import org.gem.engine.core.event.listener.det.LossRatioMeanCalculatorTest;
import org.gem.engine.core.event.listener.det.LossRatioStdDevCalculatorTest;
import org.gem.engine.core.event.listener.prob.ConditionalLossCalculatorTest;
import org.gem.engine.core.event.listener.prob.HazardCurveLoaderTest;
import org.gem.engine.core.event.listener.prob.LossCurveCalculatorTest;
import org.gem.engine.core.event.listener.prob.LossRatioCurveCalculatorTest;
import org.gem.engine.core.event.listener.prob.LossRatioExceedanceMatrixCalculatorTest;
import org.gem.engine.core.event.listener.prob.LossRatioExceedanceMatrixSegmentationCalculatorTest;
import org.gem.engine.core.event.listener.prob.MeanLossCalculatorTest;
import org.gem.engine.core.validation.AndSpecificationTest;
import org.gem.engine.core.validation.IsDataComputableTest;
import org.gem.engine.core.validation.IsHazardIMLInRangeTest;
import org.gem.engine.data.HazardCurveTest;
import org.gem.engine.data.distribution.DistributionFactoryTest;
import org.gem.engine.data.distribution.LogNormalDistributionTest;
import org.gem.engine.io.listener.ESRIAsciiWriterTest;
import org.gem.engine.io.listener.ESRIHeaderWriterTest;
import org.gem.engine.io.listener.ESRIToGTIFFConverterTest;
import org.gem.engine.io.reader.AsciiFileDiscreteVulnerabilityFunctionReaderTest;
import org.gem.engine.io.reader.AsciiFileHazardCurveReaderTest;
import org.gem.engine.io.reader.AsciiFileVulnerabilityCodeReaderTest;
import org.gem.engine.io.reader.ESRIBinaryFileAssetReaderTest;
import org.gem.engine.io.reader.ESRIBinaryFileCountryReaderTest;
import org.gem.engine.io.reader.ESRIBinaryFileExposureReaderTest;
import org.gem.engine.io.reader.OtherIntegrationTests;
import org.gem.engine.io.reader.definition.reader.HazardCurveESRIRasterFileDefinitionReaderTest;
import org.gem.engine.io.reader.definition.reader.HazardIMLESRIRasterFileDefinitionReaderTest;
import org.gem.engine.io.reader.definition.reader.StandardESRIRasterFileDefinitionReaderTest;
import org.gem.engine.io.util.BufferedPrintWriterTest;
import org.gem.engine.io.util.PrintWriterCloserTest;
import org.junit.runner.RunWith;
import org.junit.runners.Suite;
import org.junit.runners.Suite.SuiteClasses;

@RunWith(Suite.class)
@SuiteClasses( { ESRIBinaryFileExposureReaderTest.class, ESRIBinaryFileAssetReaderTest.class,
        AsciiFileVulnerabilityCodeReaderTest.class, AsciiFileDiscreteVulnerabilityFunctionReaderTest.class,
        LogNormalDistributionTest.class, DistributionFactoryTest.class, IntervalTest.class,
        BufferedPrintWriterTest.class, LossCalculatorTest.class, LossRatioCurveTest.class, ConditionalLossTest.class,
        PrintWriterCloserTest.class, ESRIHeaderWriterTest.class, AsciiFileHazardCurveReaderTest.class,
        HazardCurveTest.class, LossRatioMeanTest.class, LossRatioStdDevTest.class, LossRatioExceedanceMatrixTest.class,
        LossCurveTest.class, LossCurveCalculatorTest.class, LossRatioMeanCalculatorTest.class,
        DeterministicScenarioCacheLoaderTest.class, DeterministicScenarioCacheSynchronizerTest.class,
        HazardCurveLoaderTest.class, LossRatioExceedanceMatrixCalculatorTest.class, LossRatioCurveCalculatorTest.class,
        MeanLossTest.class, DeterministicScenarioCacheKeyTest.class, DeterministicScenarioCacheSynchronizerTest.class,
        StandardESRIRasterFileDefinitionReaderTest.class, HazardIMLESRIRasterFileDefinitionReaderTest.class,
        DiscreteVulnerabilityFunctionLoaderTest.class, DistributionLoaderTest.class,
        DiscreteVulnerabilityFunctionKeyCacheLoaderTest.class,
        DiscreteVulnerabilityFunctionKeyCacheSynchronizerTest.class, LossRatioExceedanceMatrixSegmentationTest.class,
        LossRatioExceedanceMatrixSegmentationCalculatorTest.class, HazardCurveESRIRasterFileDefinitionReaderTest.class,
        InterpolatorTest.class, ProbabilityOfOccurrenceTest.class, OtherIntegrationTests.class,
        ESRIAsciiWriterTest.class, LossRatioExceedanceMatrixProbOccTest.class, AssetLoaderTest.class,
        CountryLoaderTest.class, ESRIBinaryFileCountryReaderTest.class, MeanLossCalculatorTest.class,
        ConditionalLossCalculatorTest.class, LossRatioStdDevCalculatorTest.class, HazardIMLLoaderTest.class,
        HazardIMLRounderTest.class, ESRIToGTIFFConverterTest.class, IsDataComputableTest.class,
        AndSpecificationTest.class, ValidatorTest.class, IsHazardIMLInRangeTest.class })
public class AllTests
{

}
