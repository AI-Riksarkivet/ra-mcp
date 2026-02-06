package main

import (
	"context"
	"dagger/ra-mcp/internal/dagger"
)

// Test runs the test suite using the built container
func (m *RaMcp) Test(
	ctx context.Context,
	// +defaultPath="/"
	// +optional
	source *dagger.Directory,
) (string, error) {
	container, err := m.Build(ctx, source, "")
	if err != nil {
		return "", err
	}

	return container.
		WithExec([]string{"uv", "run", "pytest", "--cov=packages", "--cov-report=term"}).
		Stdout(ctx)
}
