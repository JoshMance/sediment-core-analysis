using Avalonia.Controls;
using Avalonia.Input;
using Avalonia.Interactivity;
using SedimentCoreApp.UI.ViewModels;

namespace SedimentCoreApp.UI.Views;

public partial class MainWindow : Window
{
    private Button? _activeToolButton;

    public MainWindow()
    {
        InitializeComponent();
        DataContext = new MainWindowViewModel();

        // Set Home button as default active
        HomeButton.Classes.Add("active");
        _activeToolButton = HomeButton;

        // Ensure maximise button glyph matches initial state
        UpdateMaxRestoreGlyph();
    }

    private void CloseButton_Click(object? sender, RoutedEventArgs e)
    {
        Close();
    }

    private void MinimizeButton_Click(object? sender, RoutedEventArgs e)
    {
        WindowState = WindowState.Minimized;
    }

    private void MaxRestoreButton_Click(object? sender, RoutedEventArgs e)
    {
        WindowState = WindowState == WindowState.Maximized
            ? WindowState.Normal
            : WindowState.Maximized;

        UpdateMaxRestoreGlyph();
    }

    private void TitleBar_PointerPressed(object? sender, PointerPressedEventArgs e)
    {
        if (e.GetCurrentPoint(this).Properties.IsLeftButtonPressed)
        {
            BeginMoveDrag(e);
        }
    }

    private void UpdateMaxRestoreGlyph()
    {
        // MaxRestoreButton is defined in XAML with x:Name
        if (MaxRestoreButton is { })
        {
            // Square for "maximise", overlapping squares for "restore"
            MaxRestoreButton.Content = WindowState == WindowState.Maximized
                ? "❐"
                : "□";
        }
    }

    private void ToolButton_Click(object? sender, RoutedEventArgs e)
    {
        if (sender is not Button clickedButton) return;

        // Don't do anything if clicking the already active button
        if (_activeToolButton == clickedButton) return;

        // Batch the class changes to reduce flicker
        if (_activeToolButton != null)
        {
            _activeToolButton.Classes.Remove("active");
        }

        clickedButton.Classes.Add("active");
        _activeToolButton = clickedButton;

        // Update ViewModel based on which button was clicked
        if (DataContext is MainWindowViewModel viewModel)
        {
            viewModel.CurrentTool = clickedButton.Name switch
            {
                "FileButton" => ActiveTool.File,
                "HomeButton" => ActiveTool.Home,
                "AnalysisButton" => ActiveTool.Analysis,
                "MappingButton" => ActiveTool.Mapping,
                "ExportButton" => ActiveTool.Export,
                _ => ActiveTool.None
            };

            // Trigger slide-in animation by temporarily setting X to -20, then back to 0
            AnimateMenuSlideIn();
        }
    }

    private async void AnimateMenuSlideIn()
    {
        // Find all menu StackPanels and trigger their transform animation
        var menuBar = this.FindControl<Grid>("MenuBar");
        if (menuBar == null) return;

        foreach (var child in menuBar.Children)
        {
            if (child is StackPanel stackPanel && stackPanel.IsVisible)
            {
                // Set starting opacity and position
                stackPanel.Opacity = 0.2;

                if (stackPanel.RenderTransform is Avalonia.Media.TranslateTransform transform)
                {
                    transform.X = -8;

                    // Small delay to ensure the transform is applied
                    await System.Threading.Tasks.Task.Delay(10);

                    // Animate to final position and opacity
                    stackPanel.Opacity = 1.0;
                    transform.X = 0;
                }
            }
        }
    }
}
