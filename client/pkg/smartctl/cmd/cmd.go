package cmd

import (
	"github.com/smart-inner/smarttune/pkg/commands"
	"github.com/smart-inner/smarttune/pkg/genericclioptions"
	"github.com/smart-inner/smarttune/pkg/smartctl/cmd/create"
	"github.com/smart-inner/smarttune/pkg/smartctl/cmd/tune"
	"github.com/spf13/cobra"
	"os"
)

type SmartctlOptions struct {
	genericclioptions.IOStreams
}

// NewDefaultSmartctlCommand creates the `smartctl` command with default arguments
func NewDefaultSmartctlCommand() *cobra.Command {
	return NewSmartctlCommand(SmartctlOptions{
		IOStreams: genericclioptions.IOStreams{In: os.Stdin, Out: os.Stdout, ErrOut: os.Stderr},
	})
}

// NewSmartctlCommand creates the `kubectl` command and its nested children.
func NewSmartctlCommand(o SmartctlOptions) *cobra.Command {
	// Parent command to which all subcommands are added.
	cmds := &cobra.Command{
		Use:   "smartctl",
		Short: "smartctl is the client of smarttune",
		Long: `smartctl is the client of smarttune, which performs configuration turing for complex systems.
Find more information at: https://github.com/smart-inner/smarttune`,
		Run: func(cmd *cobra.Command, args []string) {
			cmd.Help()
		},
		// Hook before and after Run initialize and write profiles to disk,
		// respectively.
		PersistentPreRunE: func(*cobra.Command, []string) error {
			return initProfiling()
		},
		PersistentPostRunE: func(*cobra.Command, []string) error {
			return flushProfiling()
		},
	}
	flags := cmds.PersistentFlags()
	addProfilingFlags(flags)

	groups := commands.CommandGroups{
		{
			Message: "Init Commands:",
			Commands: []*cobra.Command{
				create.NewCmdCreate(o.IOStreams),
			},
		},
		{
			Message: "Tuning Commands:",
			Commands: []*cobra.Command{
				tune.NewCmdRun(o.IOStreams),
			},
		},
	}

	groups.Add(cmds)

	return cmds
}
