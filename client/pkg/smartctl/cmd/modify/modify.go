package modify

import (
	"errors"
	"fmt"
	"github.com/smart-inner/smarttune/pkg/genericclioptions"
	"github.com/smart-inner/smarttune/util"
	"github.com/smart-inner/smarttune/util/http"
	"github.com/spf13/cobra"
	"strings"
)

type ModifyOptions struct {
	Backend      string
	Target       string
	MoreIsBetter bool
	Algorithm    string
	TuningKnobs  []string

	genericclioptions.IOStreams
}

func NewModifyOptions(streams genericclioptions.IOStreams) *ModifyOptions {
	return &ModifyOptions{
		IOStreams: streams,
	}
}

func NewCmdModify(streams genericclioptions.IOStreams) *cobra.Command {
	o := NewModifyOptions(streams)
	cmd := &cobra.Command{
		Use:   "modify SESSION_NAME --backend=backend [--target=target]",
		Short: "Modify session configuration for the specified session",
		Long: `Modify session configuration, which include tuning knobs,
tuning algorithm and target objective.`,
		Run: func(cmd *cobra.Command, args []string) {
			util.CheckErr(o.Modify(args))
		},
	}
	addModifyFlags(cmd, o)

	return cmd
}

func addModifyFlags(cmd *cobra.Command, opt *ModifyOptions) {
	cmd.Flags().StringVar(&opt.Backend, "backend", "",
		"The backend <ip:port> for smarttune server, such as '127.0.0.1:5000'")
	cmd.Flags().StringVar(&opt.Target, "target", "", "The target objective for tuning")
	cmd.Flags().BoolVar(&opt.MoreIsBetter, "more_is_better", true, "The strategy for target optimization")
	cmd.Flags().StringVar(&opt.Algorithm, "algo", "", "The algorithm for tuning")
	cmd.Flags().StringSliceVar(&opt.TuningKnobs, "tuning_knobs", []string{}, "The knobs for tuning")
}

func (o *ModifyOptions) ModifySession(url string, request map[string]interface{}) (string, error) {
	resp, err := http.PostJSON(url, request)
	if err != nil {
		return "", err
	}
	return http.HandleResponse(resp)
}

func (o *ModifyOptions) Modify(args []string) error {
	if len(args) != 1 || len(o.Backend) == 0 {
		return errors.New(fmt.Sprintf("Error: invalid subcommand "+
			"'smartctl modify %s --backend=%s'", strings.Join(args, " "), o.Backend))
	}
	request := make(map[string]interface{})
	request["name"] = args[0]
	if len(o.Algorithm) > 0 {
		request["algorithm"] = o.Algorithm
	}
	if len(o.Target) > 0 {
		request["target_objective"] = o.Target
		request["more_is_better"] = o.MoreIsBetter
	}
	if len(o.TuningKnobs) > 0 {
		request["tuning_knobs"] = o.TuningKnobs
	}

	url := fmt.Sprintf("http://%s/api/session/modify", o.Backend)
	out, err := o.ModifySession(url, request)
	if err != nil {
		return err
	}
	fmt.Fprintf(o.Out, out)
	return nil
}
