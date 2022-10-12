package register

import (
	"fmt"
	"github.com/spf13/cobra"
)

func NewCmdRegister() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "register [SESSION_NAME] [flags]",
		Short: "Register session for the specified system",
		Long: `Register session, which include system type, system version, knobs catalog, metrics catalog
tuning algorithm and target objective.`,
		Run: func(cmd *cobra.Command, args []string) {
			fmt.Println("Hello World!")
		},
	}

	return cmd
}
