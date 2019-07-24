import os
import gc
import re
from nipy import load_image
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams, cycler, transforms, patches
from matplotlib.legend_handler import HandlerLine2D, HandlerPatch
from matplotlib.collections import LineCollection
from DINGO import stats


class HandlerColorLine2D(HandlerLine2D):
    """Line will be divided into segments spaced along color map
    by number of entries in legend"""
    def __init__(self, cmap, **kw):
        self.cmap = cmap  # not a natural Line2D property
        super(HandlerColorLine2D, self).__init__(**kw)

    def create_artists(self, legend, orig_handle, xdescent, ydescent, width,
                       height, fontsize, trans):
        x = np.linspace(0, width, self.get_numpoints(legend) + 1)
        y = np.zeros(self.get_numpoints(legend) + 1) + height / 2. - ydescent
        points = np.array([x, y]).T.reshape(-1, 1, 2)
        segs = np.concatenate([points[:-1], points[1:]], axis=1)
        lc = LineCollection(segs, cmap=self.cmap, transform=trans)
        lc.set_array(x)
        lc.set_linewidth(orig_handle.get_linewidth() + 2)
        return [lc]


def add_group_lines_ci(axes, data, pvals=None, thresh=0.05, scale='red',
                       lc=(0, 0, 0.8), lw=5.0, z=1, alphal=0.8, alphaci=0.4):
    group_mean = np.ma.mean(data, 1)  # mean over t, i.e. by slice
    ci = stats.confInt(data)
    Xs = np.arange(data.shape[0])
    line = axes.plot(Xs, group_mean,
                     color=lc, linewidth=lw, zorder=z, alpha=alphal)
    patch = axes.fill_between(Xs, group_mean + ci, group_mean - ci,
                              facecolor=lc, alpha=alphaci, zorder=z)
    if pvals is not None:
        for i in range(len(Xs) - 1):
            if pvals[i] <= thresh:
                if scale == 'red':
                    pcolor = [min(1, abs(1 - (pvals[i] / thresh) + .4)), 0, 0]
                elif scale == 'green':
                    pcolor = [0, min(1, abs(1 - (pvals[i] / thresh) + .4)), 0]
            else:
                pcolor = lc
            axes.plot(Xs[i:i + 2], group_mean[i:i + 2],
                      lw=5, zorder=3, color=pcolor, solid_capstyle="round")
    return line, patch


def add_ind_lines(axes, data, ind_sort=False, lw=1, z=1, alpha=0.5):
    Xs = np.arange(data.shape[0])
    if ind_sort:
        ind_mean = np.ma.mean(data, 0)
        sort = np.argsort(ind_mean)  # sort by average fa per person
        Ys = data[:, sort]
    else:
        Ys = data
    lines = axes.plot(Xs, Ys, linewidth=lw, zorder=z, alpha=alpha)
    return lines


def add_ind_labels(figure, axes, data, ind_labels):
    txt_offset = transforms.offset_copy(axes.transData, fig=figure,
                                        x=0.02, y=0.05, units='inches')
    ind_peaks_idx = zip(np.argmax(data, 0), np.arange(data.shape[1]))
    # zip(slice of max fa by individual, number of individual)
    labels = []
    for x, ind in ind_peaks_idx:
        labels.append(plt.text(x, data[x, ind], ind_labels[ind],
                               fontsize=10,
                               transform=txt_offset))
    return labels


def plot_along(data, data2=None, pvals=None, thresh=0.05, scale='red',
               title='FA Along Tract', legend=None, xlim=None, ylim=(0, 1),
               xlabel='Unknown Dir', ylabel='FA',
               fig_facecolor=(1, 1, 1), fig_size=(15, 5),
               bg_color=(0, 0, 0), bg_alpha=0.25,
               lcolor=(0, 0, 0.8), lcolor2=(0, 0.8, 0),
               ind_sort=None, ind_labels=None, ind_cmap=None, ind_cmap2=None,
               filename='FA_along_tract', ):
    """Plot along tract FA values, either means or individuals separately.
    Data input is a 2-D numpy masked array
    
    Parameters
    ----------
    data            :   2-D numpy array - Mandatory
    data2           :   2-D numpy array
    pvals           :   1-D numpy array
    thresh          :   Float - alpha threshold - default 0.05
    scale           :   Str - default 'red'
    title           :   Str - default 'FA Along Tract'
    legend          :   Tuple - does not apply to ind, default ('Mean', '95%CI')
    xlim            :   2-sequence -default (0, data.shape[0])
    ylim            :   2-sequence -default (0, 1)
    xlabel          :   Str - default 'Unknown Dir'
    ylabel          :   Str - default 'FA'
    fig_facecolor   :   3-sequence - figure background color - default (1,1,1)
    fig_size        :   2-sequence - figure size - default (15,5)
    bg_color        :   3-sequence - axis background color - default (0,0,0)
    bg_alpha        :   Float - axis background alpha - default 0.25
    lcolor          :   3-sequence - mean line color - default (0,0,0.8)
    lcolor2         :   3-sequence - mean line 2 color - default (0,0.8,0)
    ind_sort        :   Bool - default None i.e. plot group mean, otherwise
        whether to sort individual along tract fas in the colorspace by mean
    ind_labels      :   Sequence (Str,) same length as data
    ind_cmap        :   Str - colormap name - default 'plasma'
    ind_cmap2       :   Str - colormap name - default 'PuBuGn'
    filename        :   Str - save filename - default 'FA_along_tract'
    
    Return
    ------
    matplotlib.pyplot.figure
    savefile image at filename"""
    if xlim is None:
        xlim = (0, data.shape[0])

    if legend is None:
        legend = ('Mean', '95% CI')

    if len(data.shape) != 2:
        raise (ValueError('data must be 2-D, but has shape {}'.format(data.shape, )))

    fig = plt.figure(
        facecolor=fig_facecolor,
        figsize=fig_size)
    sub = fig.add_subplot(111,  # 1st figure 1x1
                          facecolor=bg_color,
                          xlim=xlim,
                          ylim=ylim)
    sub.set_title(title,
                  fontsize=14,
                  fontweight='bold')
    sub.set_xlabel(''.join(('Slice: ', xlabel)),
                   fontsize=14,
                   fontweight='bold')
    sub.set_ylabel(ylabel,
                   fontsize=14,
                   fontweight='bold')
    sub.patch.set_alpha(bg_alpha)

    Xs = np.arange(data.shape[0])

    if ind_sort is None:  # plot mean, confidence interval
        if pvals is not None and len(pvals) != len(data):
            # add pvals to plot
            raise (ValueError('data and pvals must have the same length'
                              'Data: {:d}, Pvals: {:d}'
                              .format(len(data), len(pvals))))
        g1_line, g1_patch = add_group_lines_ci(sub, data, pvals,  # sig on g1 line
                                               thresh=thresh, scale=scale,
                                               lc=lcolor, lw=5.0, z=1,
                                               alphal=0.8, alphaci=0.4)
        if data2 is not None:
            g2_line, g2_patch = add_group_lines_ci(sub, data2,
                                                   lc=lcolor2, lw=5.0, z=2,
                                                   alphal=0.8, alphaci=0.4)
            plt.legend(handles=[g1_line[0], g2_line[0], g1_patch, g2_patch],
                       labels=legend)
        else:
            plt.legend(handles=[g1_line[0], g1_patch], labels=legend)
    else:  # plot individual lines
        if ind_cmap is None:
            cmap = plt.get_cmap('plasma')
        else:
            cmap = plt.get_cmap(ind_cmap)
        if ind_cmap2 is None:
            cmap2 = plt.get_cmap('PuBuGn')
        else:
            cmap2 = plt.get_cmap(ind_cmap2)

        color1 = cmap(np.linspace(0, 1, data.shape[1]))
        ind_lines1 = add_ind_lines(sub, data, ind_sort, 1, 1, 0.5)
        if data2 is not None:
            color2 = cmap2(np.linspace(0, 1, data2.shape[1]))
            colors = np.concatenate((color1, color2), 0)
            ind_lines2 = add_ind_lines(sub, data2, ind_sort, 1, 1, 0.5)
            ind_lines = ind_lines1 + ind_lines2
            plt.legend(handles=[ind_lines1[0], ind_lines2[0]],
                       labels=legend,
                       handler_map={
                           ind_lines1[0]: HandlerColorLine2D(cmap=cmap, numpoints=4),
                           ind_lines2[0]: HandlerColorLine2D(cmap=cmap2, numpoints=4)})
        else:
            colors = color1
            ind_lines = ind_lines1
            plt.legend(handles=[ind_lines1[0]],
                       labels=legend,
                       handler_map={
                           ind_lines1[0]: HandlerColorLine2D(cmap=cmap, numpoints=4)})
        plt.gca().set_prop_cycle(cycler(color=colors))  # distribute in cmap
        for i, j in enumerate(ind_lines):
            j.set_color(colors[i])

        if ind_labels is not None:
            if data2 is None:
                if len(ind_labels) != data.shape[1]:
                    raise (ValueError('data and labels must have the same length'
                                      'Data {:d}, Labels: {:d}'
                                      .format(data.shape[1], len(ind_labels))))
                else:
                    i1_labels = add_ind_labels(fig, sub, data, ind_labels)
            else:
                if len(ind_labels[0]) != data.shape[1]:
                    raise (ValueError('data and labels must have the same length'
                                      'Data {:d}, Labels: {:d}'
                                      .format(data.shape[1], len(ind_labels[0]))))
                if len(ind_labels[1]) != data2.shape[1]:
                    raise (ValueError('data and labels must have the same length'
                                      'Data2 {:d}, Labels: {:d}'
                                      .format(data2.shape[1], len(ind_labels[1]))))
                else:
                    i1_labels = add_ind_labels(fig, sub, data, ind_labels[0])
                    i2_labels = add_ind_labels(fig, sub, data2, ind_labels[1])

    plt.savefig(filename,
                dpi=900,
                facecolor=fig.get_facecolor(),
                edgecolor='w',
                orientation='landscape',
                bbox_inches=None,
                pad_inches=0.1)
    plt.close(fig)


def get_data(filename):
    """Load a nifti and return its data as an array
    Parameters
    ----------
    filename    :   Str
    
    Return
    ------
    data        :   numpy.array"""
    data_nii = load_image(filename)
    return data_nii.get_data()


def mask_data(data_filename, mask_filename):
    """Mask data, keep points where mask = 1
    Parameters
    ----------
    data_filename   :   Str
    mask_filename   :   Str
    
    Return
    ------
    masked_data     :   numpy.ma.masked_array"""
    data = get_data(data_filename)
    mask = get_data(mask_filename)

    if data.shape != mask.shape:
        raise (LookupError('Data and mask do not have the same dimensions.'
                           '\nData: {}, Mask: {}'
                           .format(data.shape, mask.shape)))
    else:
        np_mask = np.ma.make_mask(mask)
        ext_mask = np.invert(np_mask)
        masked_data = np.ma.masked_array(data, ext_mask)
    return masked_data


def mean_data(data, collapse=None):
    """Wrap np.ma.mean to average over multiple dimensions. May provide 
    dimensions by index or as a boolean sequence of len(data.shape).
    If none provided will average over all.
    Parameters
    ----------
    data        :   masked array
    collapse    :   tuple,list,array - ints or booleans
    
    Return
    ------
    mean_data   :  data averaged over given or all dimensions"""
    if collapse is None:
        # no dimensions given, return one value
        mean_data = np.ma.mean(data)
    elif isinstance(collapse, int) and collapse < len(data.shape):
        # one dim given, average it
        mean_data = np.ma.mean(data, collapse)
    elif len(data.shape) != len(collapse):
        if all([isinstance(c, int) for c in collapse]):
            # dim by index, average them
            if any([c > len(data.shape) - 1 for c in collapse]):
                # could let numpy throw the error, but this may save time
                msg = ('Data axis {:d} is out of bounds for array of dimension {:d}'
                       .format(c, len(data.shape)))
                raise (IndexError(msg))
            mean_data = data
            for direction in sorted(collapse, reverse=True):
                # big->little dim mean order for proper indices
                mean_data = np.ma.mean(mean_data, direction)
        else:
            # dimensions not given by index, but improper
            msg = ('boolean collapse must be the same length as data.shape'
                   '\nData: {:d}, Collapse: {:d}'
                   .format(len(data.shape), len(collapse)))
            raise (LookupError(msg))
    else:
        # dim by boolean, big->little dim mean order for proper indices
        mean_data = data
        for direction in range(len(collapse), 0, -1):
            if collapse[direction - 1]:
                mean_data = np.ma.mean(mean_data, direction - 1)
    return mean_data


def mean_3d(data):
    """produce separate means for each slice direction"""
    means = [None] * 3
    for i in range(0, 3):
        collapse = tuple({0, 1, 2} - {i})
        means[i] = mean_data(data, collapse)
    return means


tract2dir = {
    'CCBody': 'R-L',
    'Genu': 'R-L',
    'Splenium': 'R-L',
    'CST_L': 'I-S',
    'CST_R': 'I-S',
    'FOF_L': 'P-A',
    'FOF_R': 'P-A',
    'ILF_L': 'P-A',
    'ILF_R': 'P-A',
    'SLF_L': 'P-A',
    'SLF_R': 'P-A'
}

dir2mean = {
    'R-L': (0, 1, 1, 0),
    'I-S': (1, 1, 0, 0),
    'P-A': (1, 0, 1, 0)
}


def labels_from_filelist(filelist, looking_for=None, prefix=None, suffix=None):
    with open(filelist, 'r') as f:
        files = f.read().splitlines()
    if looking_for is None:
        looking_for = '([\w-]*)'
    if prefix is None:
        prefix = '(?<=\/_included_ids_)'
    if suffix is None:
        suffix = '(?=\/)'
    ids = []
    for afile in files:
        s = re.search(
            ''.join((prefix, looking_for, suffix)),
            afile)
        # if search not successful will raise attribute error
        try:
            if len(s.groups()) == 1:
                ids.append(s.group(1))
            else:
                raise (ValueError('Expected one match, found {}'.format(s.groups())))
        except AttributeError as err:
            print('file {}: {}'.format(files.index(afile), afile))
            raise
    if len(ids) == len(files):
        return ids
    else:
        return None


def gen_tract_plot(fa_filename, mask_filename, tract, prefix=None, ylim=None,
                   direction=None, filelist=None, labels=None, ind_sort=True):
    """Generate XYZ mean and individual along tract fa plots
    Samples each voxel of fa, where mask = 1
    
    Parameters
    ----------
    fa_filename     :   Str - t merged fa maps for all individuals
    mask_filename   :   Str - t merged mask, 1 for presence of tract, 0 for not
    tract           :   Str - tract name, for title and save filename
    direction       :   Str - optional for std tracts, 1 of ('R-L','I-S','P-A')
    filelist        :   Str - optional file with list of included files
        each file has 'tract_individual_scan' in filename from which to get ids
    labels          :   Seq - optional sequence of ids to supply directly
    
    Return
    ------
    FA x Slice Images for means w/ confidence intervals and sorted individuals
    """
    if direction is None:
        direction = tract2dir[tract]
    if ylim is None:
        ylim = (0.0, 0.7)
    if prefix is None:
        data_savename = ''.join(('FA_along_',
                                 tract,
                                 '_',
                                 direction,
                                 '.csv'))
        chart_title = ' '.join(('FA Along', tract))
        chart_savename = '_'.join(('FA_along',
                                   tract,
                                   direction))
        chart_ind_savename = '_'.join(('FA_along',
                                       tract,
                                       direction,
                                       'ind'))
        chart_labeled_savename = '_'.join(('FA_along',
                                           tract,
                                           direction,
                                           'ind_labeled'))
    else:
        data_savename = ''.join((prefix,
                                 '_FA_along_',
                                 tract, '_',
                                 direction,
                                 '.csv'))
        chart_title = ' '.join((prefix, 'FA Along', tract))
        chart_savename = '_'.join((prefix,
                                   'FA_along',
                                   tract,
                                   direction))
        chart_ind_savename = '_'.join((prefix,
                                       'FA_along',
                                       tract,
                                       direction,
                                       'ind'))
        chart_labeled_savename = '_'.join((prefix,
                                           'FA_along',
                                           tract,
                                           direction,
                                           'ind_labeled'))

    print('Masking {}'.format(tract))
    masked_fa = mask_data(fa_filename, mask_filename)
    print('Averaging {} to keep {} slices'.format(tract, direction))
    fa_slice_means = mean_data(masked_fa, dir2mean[direction])
    masked_fa = None
    gc.collect()

    np.savetxt(
        data_savename,
        fa_slice_means,
        delimiter=',')

    print('Generating {} group plot'.format(tract))
    plot_along(
        fa_slice_means,
        xlabel=tract2dir[tract],
        title=chart_title,
        filename=chart_savename,
        ylim=ylim)
    print('Generating {} ind plot'.format(tract))
    plot_along(
        fa_slice_means,
        xlabel=tract2dir[tract],
        title=chart_title,
        filename=chart_ind_savename,
        ylim=ylim,
        ind_sort=ind_sort)

    input_labels = None
    if filelist is not None:
        input_labels = labels_from_filelist(filelist)
    elif labels is not None:
        input_labels = labels
    if input_labels is not None:
        print('Generating {} ind_labeled plot'.format(tract))
        plot_along(
            fa_slice_means,
            xlabel=tract2dir[tract],
            title=chart_title,
            filename=chart_labeled_savename,
            ylim=ylim,
            ind_sort=ind_sort,
            ind_labels=input_labels)


def gen_2group_tract_plots(g1_fa, g1_mask, g2_fa, g2_mask, tract, legend):
    """Generate along tract fa plots with slices marked for significance
    between two groups
    
    Parameters
    ----------
    g1_fa       :   Str - t merged fa maps for group 1
    g1_mask     :   Str - t merged group 1 masks, 1 for tract, 0 for not
    g2_fa       :   Str - t merged fa maps for group 2
    g2_mask     :   Str - t merged group 2 masks, 1 for tract, 0 for not
    tract       :   Str - tract name, for tile and save filename
    
    Return
    ------
    FA x Slice Images for means w/ confidence intervals and significant
        differences highlighted
    """

    t_g1 = ' '.join((tract, legend[0]))
    print('Masking {}'.format(t_g1))
    masked_g1 = mask_data(g1_fa, g1_mask)
    print('Masked {}'.format(t_g1))
    print('Averaging {} to keep {} slices'.format(t_g1, tract2dir[tract]))
    g1_slice_means = mean_data(masked_g1, dir2mean[tract2dir[tract]])
    print('Averaged {}'.format(t_g1))
    masked_g1 = None
    gc.collect()
    # masked arrays are very large, prefer to get them out of memory and not end
    # up using swap
    t_g2 = ' '.join((tract, legend[1]))
    print('Masking {}'.format(t_g2))
    masked_g2 = mask_data(g2_fa, g2_mask)
    print('Masked {}'.format(t_g2))
    print('Averaging {} slices to keep {}'.format(t_g2, tract2dir[tract]))
    g2_slice_means = mean_data(masked_g2, dir2mean[tract2dir[tract]])
    print('Averaged {}'.format(t_g2))
    masked_g2 = None
    gc.collect()

    np.savetxt(
        ''.join(('FA_along_', tract, '_', tract2dir[tract], '_',
                 legend[0].replace(' ', '_')
                 , '.csv')),
        g1_slice_means,
        delimiter=',')
    np.savetxt(
        ''.join(('FA_along_', tract, '_', tract2dir[tract], '_',
                 legend[1].replace(' ', '_')
                 , '.csv')),
        g2_slice_means,
        delimiter=',')

    print('Calculating significant differences by slice')
    pvals = np.array(stats.stepdown_adjust(g1_slice_means, g2_slice_means,
                                           teststat='welcht', resample_func='permute', permutes=1000))

    np.savetxt(
        ''.join(('Pvals_stepdown_adjust_', tract, '_', tract2dir[tract], '.csv')),
        pvals,
        delimiter=',')
    print('Generating sig plot')
    plot_along(g1_slice_means, g2_slice_means, pvals,
               xlabel=tract2dir[tract],
               title=' '.join(('FA Along', tract)),
               legend=legend,
               filename='_'.join(('FA_along', tract, tract2dir[tract], 'sig')),
               ylim=(0, 0.6)
               )
    print('Generating ind plot')
    plot_along(g1_slice_means, g2_slice_means,
               xlabel=tract2dir[tract],
               title=' '.join(('FA Along', tract, 'ind_sorted')),
               legend=legend[0:2],
               filename='_'.join(('FA_along', tract, tract2dir[tract],
                                  'ind_sorted')),
               ylim=(0, 0.6),
               ind_sort=True
               )


def gen_along_tract_means(fa_filename, mask_filename, tract):
    masked_fa = mask_data(fa_filename, mask_filename)
    fa_slice_means = mean_3d(masked_fa)
    masked_fa = None
    gc.collect()
    direction = (
        'R-L',
        'P-A',
        'I-S')
    for i in range(0, 3):
        np.savetxt(
            ''.join(('FA_along_', tract, '_', direction[i], '.txt')),
            fa_slice_means[i],
            delimiter=',')