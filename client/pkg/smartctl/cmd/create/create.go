package create

import (
	"fmt"
	"github.com/spf13/cobra"
)

func NewCmdCreate() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "create [SESSION_NAME] [flags]",
		Short: "Create session for the specified system",
		Long: `Create session, which include system type, system version, knobs catalog, metrics catalog
tuning algorithm and target objective.`,
		Run: func(cmd *cobra.Command, args []string) {
			fmt.Println("Hello Creating!")
		},
	}

	return cmd
}
