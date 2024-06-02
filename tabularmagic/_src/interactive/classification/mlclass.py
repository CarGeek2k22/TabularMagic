import pandas as pd
import matplotlib.axes as axes
import matplotlib.figure as figure
from typing import Iterable, Literal
from ...ml.discriminative.classification.base_classification import \
    BaseClassification
from ...metrics.classification_scoring import ClassificationBinaryScorer
from ...data.datahandler import DataHandler
from ..visualization import plot_roc_curve
from ...util.console import print_wrapped




class SingleModelSingleDatasetMLClassReport:
    """
    SingleModelSingleDatasetMLClassReport: generates classification-relevant plots and
    tables for a single machine learning model on a single dataset.
    """

    def __init__(self, model: BaseClassification,
                 dataset: Literal['train', 'test']):
        """
        Initializes a SingleModelSingleDatasetMLClassReport object.

        Parameters
        ----------
        - model: BaseClassification. The data for the model must already be
            specified. The model should already be trained on the
            specified data.
        - dataset: Literal['train', 'test'].
        """
        self.model = model
        self._is_binary = isinstance(model.train_scorer, 
                                     ClassificationBinaryScorer)
        if dataset not in ['train', 'test']:
            raise ValueError('dataset must be either "train" or "test".')
        self._dataset = dataset


    def fit_statistics(self) -> pd.DataFrame:
        """Returns a DataFrame containing the evaluation metrics
        for the model on the specified data.

        Returns
        -------
        - pd.DataFrame
        """
        if self._dataset == 'train':
            return self.model.train_scorer.stats_df()
        else:
            return self.model.test_scorer.stats_df()
        

    def fit_statistics_by_class(self) -> pd.DataFrame:
        """Returns a DataFrame containing the evaluation metrics
        for the model on the specified data, broken down by class.

        Returns
        -------
        - pd.DataFrame
        """
        if self._is_binary:
            print_wrapped('Fit statistics by class are not ' +\
                'available for binary classification.', type='WARNING')
            return None

        if self._dataset == 'train':
            return self.model.train_scorer.stats_by_class_df()
        else:
            return self.model.test_scorer.stats_by_class_df()


    def cv_fit_statistics(self, 
                          averaged_across_folds: bool = True) -> pd.DataFrame:
        """Returns a DataFrame containing the cross-validated evaluation metrics
        for the model on the specified data.

        Parameters
        ----------
        - averaged_across_folds : bool. If True, returns a DataFrame 
            containing goodness-of-fit statistics across all folds.

        Returns
        -------
        - pd.DataFrame | None. None is returned if cross validation 
            fit statistics are not available.
        """
        if not self.model._is_cross_validated():
            print_wrapped('Cross validation statistics are not available ' +\
                'for models that are not cross-validated.', type='WARNING')
            return None
        if self._dataset == 'train':
            if averaged_across_folds:
                return self.model.cv_scorer.stats_df()
            else:
                return self.model.cv_scorer.cv_stats_df()
        elif self._dataset == 'test':
            print_wrapped(
                'Cross validation statistics are not available for test data.',
                type='WARNING')
            return None
        

    def cv_fit_statistics_by_class(self, 
                                   averaged_across_folds: bool = True) -> pd.DataFrame:
        """Returns a DataFrame containing the cross-validated evaluation metrics
        for the model on the specified data, broken down by class.

        Returns
        -------
        - pd.DataFrame
        """
        if not self.model._is_cross_validated():
            print_wrapped('Cross validation statistics are not available ' +\
                'for models that are not cross-validated.', type='WARNING')
            return None

        if self._is_binary:
            print_wrapped('Cross validation statistics by class are not ' +\
                'available for binary classification.', type='WARNING')
            return None

        if self._dataset == 'train':
            if averaged_across_folds:
                return self.model.cv_scorer.stats_by_class_df()
            else:
                return self.model.cv_scorer.cv_stats_by_class_df()
        else:
            print_wrapped(
                'Cross validation statistics are not available for test data.',
                type='WARNING')
            return None
        

    def plot_roc_curve(self, figsize: Iterable = (5, 5),
                       ax: axes.Axes = None) -> figure.Figure:
        """Returns a figure that is the ROC curve for the model.

        Parameters
        ----------
        - figsize: Iterable.
        - ax: Axes.

        Returns
        -------
        - Figure
        """
        if not self._is_binary:
            print_wrapped('ROC curve is not available for ' +\
                'multiclass classification.', type='WARNING')
            return None

        if self._dataset == 'train':
            if self.model.train_overall_scorer is not None:
                # in case of nested cross validation, use overall scorer
                y_score = self.model.train_overall_scorer._y_pred_score
                y_true = self.model.train_overall_scorer._y_true
            else:
                y_score = self.model.train_scorer._y_pred_score
                y_true = self.model.train_scorer._y_true
        else:
            y_score = self.model.test_scorer._y_pred_score
            y_true = self.model.test_scorer._y_true
        return plot_roc_curve(y_score, y_true, figsize, ax)


class SingleModelMLClassReport:
    """SingleModelMLClassReport: simple class for routing to appropriate 
    SingleModelSingleDatasetMLClassReport object.
    """

    def __init__(self, model: BaseClassification):
        """
        Initializes a SingleModelMLClassReport object.

        Parameters
        ----------
        - model: BaseClassification. The data for the model must already be
            specified. The model should already be trained on the
            specified data.
        """
        self.model = model

    def train_report(self) -> SingleModelSingleDatasetMLClassReport:
        """Returns a SingleModelSingleDatasetMLClassReport 
            object for the training data.

        Returns
        -------
        - SingleModelSingleDatasetMLClassReport
        """
        return SingleModelSingleDatasetMLClassReport(self.model, 'train')

    def test_report(self) -> SingleModelSingleDatasetMLClassReport:
        """Returns a SingleModelSingleDatasetMLClassReport
          object for the test data.

        Returns
        -------
        - SingleModelSingleDatasetMLClassReport
        """
        return SingleModelSingleDatasetMLClassReport(self.model, 'test')



class MLClassificationReport:
    """MLClassificationReport.
    Fits the model based on provided DataHandler.
    Wraps train and test SingleDatasetMLClassReport objects.
    """

    def __init__(self, 
                 models: Iterable[BaseClassification],
                 datahandler: DataHandler,
                 y_var: str,
                 X_vars: Iterable[str],
                 outer_cv: int = None,
                 outer_cv_seed: int = 42,
                 verbose: bool = True):
        """MLClassificationReport.
        Fits the model based on provided DataHandler.
        Wraps train and test SingleDatasetMLClassReport objects.

        Parameters
        ----------
        - models: Iterable[BaseClassification].
            The BaseClassification models must already be trained.
        - datahandler: DataHandler.
            The DataHandler object that contains the data.
        - y_var : str.
            The name of the dependent variable.
        - X_vars : Iterable[str].
            The names of the independent variables.
        - outer_cv: int.
            If not None, reports training scores via nested k-fold CV.
        - outer_cv_seed: int.
            The random seed for the outer cross validation loop.
        - verbose: bool.
        """
        self._models: list[BaseClassification] = models
        self._id_to_model = {model._name: model for model in models}

        self.y_var = y_var
        self.X_vars = X_vars

        self._emitter = datahandler.train_test_emitter(
            y_var=y_var,
            X_vars=X_vars
        )
        self._emitters = None
        if outer_cv is not None:
            self._emitters = datahandler.kfold_emitters(
                y_var=y_var,
                X_vars=X_vars,
                n_folds=outer_cv,
                shuffle=True,
                random_state=outer_cv_seed
            )
            
        self._verbose = verbose
        for model in self._models:
            if self._verbose:
                print_wrapped(f'Fitting model {model._name}.',
                               type='UPDATE')
            model.specify_data(dataemitter=self._emitter, 
                               dataemitters=self._emitters)
            model.fit()
            if self._verbose:
                print_wrapped(f'Fitted model {model._name}.',
                               type='UPDATE')

        self._id_to_report = {model._name: SingleModelMLClassReport(model)
                              for model in models}

    
    def model_report(self, model_id: str) -> SingleModelMLClassReport:
        """Returns the SingleModelMLClassReport object for the specified model.

        Parameters
        ----------
        - model_id: str. The id of the model.

        Returns
        -------
        - SingleModelMLClassReport
        """
        return self._id_to_report[model_id]
    

    def model(self, model_id: str) -> BaseClassification:
        """Returns the model with the specified id.

        Parameters
        ----------
        - model_id: str. The id of the model.

        Returns
        -------
        - BaseClassification
        """
        return self._id_to_model[model_id]

    def fit_statistics(self, dataset: Literal['train', 'test']) -> pd.DataFrame:
        """Returns a DataFrame containing the evaluation metrics for
        all models on the specified data.

        Parameters
        ----------
        - dataset: Literal['train', 'test'].

        Returns
        -------
        - pd.DataFrame
        """
        if dataset == 'train':
            return pd.concat([report.train_report().fit_statistics()
                              for report in self._id_to_report.values()],
                              axis=1)
        else:
            return pd.concat([report.test_report().fit_statistics()
                              for report in self._id_to_report.values()],
                              axis=1)
        
    def cv_fit_statistics(self, 
                          averaged_across_folds: bool = True) -> pd.DataFrame:
        """Returns a DataFrame containing the evaluation metrics for
        all models on the training data. Cross validation must have been 
        specified; otherwise an error will be thrown.

        Parameters
        ----------
        - averaged_across_folds : bool. If True, returns a DataFrame 
            containing goodness-of-fit statistics across all folds.

        Returns
        -------
        - pd.DataFrame | None. None is returned if cross validation
        """
        if not self._models[0]._is_cross_validated():
            print_wrapped('Cross validation statistics are not available ' +\
                'for models that are not cross-validated.', type='WARNING')
            return None
        return pd.concat([report.train_report().\
                          cv_fit_statistics(averaged_across_folds) \
                            for report in self._id_to_report.values()],
                            axis=1)


    def __getitem__(self, model_id: str) -> SingleModelMLClassReport:
        return self._id_to_report[model_id]
    


    